"""Phase 2: deterministic credit + fraud orchestration for Micro Business Loans.

This module is intentionally policy-driven and explainable. It does not make a
final lending decision from an opaque model: every score, hard-stop and source
field is returned for auditability.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from .db_models import (
    CustomerRecord, CustomerBusinessRecord, CustomerKYCRecord,
    CustomerBankAccountRecord, CustomerRiskProfileRecord, LoanRecord,
    BankTransactionRecord,
)
from .mbl_scorecard import calculate
from .phase1_customer import fingerprint, potential_duplicates, record_customer_event


def _num(v, default=0.0):
    try: return float(v)
    except (TypeError, ValueError): return default


def _bool(v):
    return bool(v) if v is not None else None


def build_assessment_input(db: Session, customer_id: int, loan: LoanRecord | None = None) -> dict[str, Any]:
    c = db.get(CustomerRecord, customer_id)
    if not c: raise ValueError("customer_not_found")
    b = db.query(CustomerBusinessRecord).filter(CustomerBusinessRecord.customer_id == customer_id).order_by(CustomerBusinessRecord.id.desc()).first()
    k = db.query(CustomerKYCRecord).filter(CustomerKYCRecord.customer_id == customer_id).first()
    bank = db.query(CustomerBankAccountRecord).filter(CustomerBankAccountRecord.customer_id == customer_id, CustomerBankAccountRecord.is_primary.is_(True)).first()
    tx = db.query(BankTransactionRecord).filter(BankTransactionRecord.customer_id == customer_id).order_by(BankTransactionRecord.id.desc()).limit(500).all()
    credits = [float(x.amount or 0) for x in tx if str(x.direction).lower() in {"credit", "cr", "in"}]
    debits = [float(x.amount or 0) for x in tx if str(x.direction).lower() in {"debit", "dr", "out"}]
    avg_credits = (sum(credits) / max(len(credits), 1)) * 20 if credits else _num(c.monthly_income) * 2
    gaming = any("gambl" in str(x.description or "").lower() or "casino" in str(x.description or "").lower() for x in tx)
    stock = sum(1 for x in tx if any(t in str(x.description or "").lower() for t in ("zerodha", "groww", "upstox", "angel one", "sharekhan", "nse", "bse")))
    dup = potential_duplicates(db, pan=c.pan, mobile=c.mobile, email=c.email)
    age = 0
    if c.date_of_birth:
        try:
            dob = datetime.strptime(str(c.date_of_birth)[:10], "%Y-%m-%d")
            age = max(0, int((datetime.now() - dob).days / 365.25))
        except ValueError: pass
    return {
        "ownership_proof": c.residence_ownership or "",
        "business_owned": str(b.ownership_type or "").lower() in {"owned", "own", "applicant"} if b else False,
        "residence_owned": str(c.residence_ownership or "").lower() in {"owned", "own", "self"},
        "business_geography": "",
        "age": age,
        "cibil_unsecured_enquiries_30d": 0,
        "cibil_repayment": "clean" if _num(c.cibil_score) >= 700 else "",
        "cibil_adverse_last_3y": False,
        "unsecured_loans_50k_plus": 0,
        "avg_monthly_bank_credits": avg_credits,
        "bank_bounces_3m": 0,
        "aqb": max([_num(x.balance) for x in tx if x.balance is not None] or [_num(c.average_bank_balance)]),
        "ecs_returns_12m": 0,
        "business_type": b.business_type if b else c.business_type,
        "business_vintage_years": b.business_vintage_years if b else c.years_in_business,
        "business_stock": 0,
        "monthly_emi_obligation": c.existing_emi,
        "foir": c.foir,
        "trade_validations": 0,
        "gst_years": 0,
        "gstr3b_avg_monthly_turnover": b.monthly_turnover if b else 0,
        "itr_income": _num(c.monthly_income) * 12,
        "mobile_stability_years": 0,
        "active_dpd_overdue": False,
        "writeoff_last_3y": False,
        "settlement_last_3y": False,
        "suit_filed_last_5y": False,
        "gaming_transactions_3m": gaming,
        "stock_market_transactions_3m": stock,
        "business_address_geo_verified": None,
        "residence_address_geo_verified": None,
        "monthly_income": c.monthly_income,
        "existing_emi": c.existing_emi,
        "bureau_score": c.cibil_score,
        "banking_score": None,
        "primary_bank_verified": bool(bank and str(bank.verification_status).lower() in {"verified", "success"}),
        "kyc_verified": bool(k and str(k.status).lower() in {"verified", "completed"}),
        "duplicate_customer_ids": [x for x in dup if x != customer_id],
        "transaction_count": len(tx),
        "credit_transaction_count": len(credits),
        "debit_transaction_count": len(debits),
    }


def fraud_screen(i: dict[str, Any]) -> dict[str, Any]:
    flags: list[str] = []
    if i.get("duplicate_customer_ids"): flags.append("POTENTIAL_DUPLICATE_CUSTOMER")
    if i.get("gaming_transactions_3m"): flags.append("GAMING_TRANSACTIONS")
    if _num(i.get("stock_market_transactions_3m")) > 10: flags.append("HIGH_STOCK_MARKET_ACTIVITY")
    if i.get("business_address_geo_verified") is False: flags.append("BUSINESS_GEO_NOT_VERIFIED")
    if i.get("residence_address_geo_verified") is False: flags.append("RESIDENCE_GEO_NOT_VERIFIED")
    if not i.get("kyc_verified"): flags.append("KYC_NOT_VERIFIED")
    if not i.get("primary_bank_verified"): flags.append("PRIMARY_BANK_NOT_VERIFIED")
    return {"status": "REVIEW" if flags else "CLEAR", "flags": flags, "flag_count": len(flags)}


def assess(db: Session, customer_id: int, loan_id: int | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    loan = db.get(LoanRecord, loan_id) if loan_id else db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan: raise ValueError("loan_request_not_found")
    if loan.customer_id != customer_id: raise ValueError("loan_customer_mismatch")
    inputs = build_assessment_input(db, customer_id, loan)
    if overrides: inputs.update(overrides)
    fraud = fraud_screen(inputs)
    score_result = calculate(inputs)
    hard = list(score_result.hard_rejects)
    if fraud["status"] == "REVIEW" and "fraud_review_required" not in hard: hard.append("fraud_review_required")
    if hard:
        decision = "REJECT" if any(x in score_result.hard_rejects for x in hard) else "MANUAL_REVIEW"
        approval = 0
    else:
        decision, approval = score_result.decision, score_result.approval_percent
    loan.status = "rejected" if decision == "REJECT" else "assessment"
    loan.current_stage = "REJECTED" if decision == "REJECT" else "ASSESSMENT"
    loan.eligible_amount = 0 if approval == 0 else int(round(float(loan.requested_amount or 0) * approval / 100))
    loan.scorecard_score = score_result.score
    loan.scorecard_max = score_result.max_score
    loan.scorecard_version = score_result.version
    loan.scorecard_decision = decision
    loan.scorecard_approval_percent = approval
    loan.scorecard_reasons = json.dumps(list(dict.fromkeys(score_result.reasons + fraud["flags"])), ensure_ascii=False)
    loan.scorecard_hard_rejects = json.dumps(list(dict.fromkeys(hard)), ensure_ascii=False)
    loan.scorecard_factor_scores = json.dumps(score_result.factor_scores, ensure_ascii=False)
    risk = db.query(CustomerRiskProfileRecord).filter(CustomerRiskProfileRecord.customer_id == customer_id).first()
    if not risk: risk = CustomerRiskProfileRecord(customer_id=customer_id); db.add(risk)
    risk.risk_status = "high" if decision == "REJECT" else "review" if decision == "MANUAL_REVIEW" else "assessed"
    risk.fraud_status = fraud["status"].lower()
    risk.credit_status = decision.lower()
    risk.risk_grade = "H" if decision == "REJECT" else "M" if decision == "MANUAL_REVIEW" else "L"
    risk.risk_flags = json.dumps(fraud["flags"], ensure_ascii=False)
    risk.last_assessed_at = datetime.now(timezone.utc)
    record_customer_event(db, customer_id, "CREDIT_ASSESSMENT_COMPLETED", details={"loan_id": loan.id, "decision": decision, "score": score_result.score, "fraud_status": fraud["status"]})
    db.commit(); db.refresh(loan); db.refresh(risk)
    return {"loan_id": loan.id, "customer_id": customer_id, "inputs": inputs, "credit": score_result.payload() | {"decision": decision, "approval_percent": approval, "eligible_amount": loan.eligible_amount}, "fraud": fraud, "risk_profile": {"risk_grade": risk.risk_grade, "risk_status": risk.risk_status, "fraud_status": risk.fraud_status, "credit_status": risk.credit_status}}
