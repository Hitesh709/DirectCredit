"""Phase 2 credit + fraud orchestration with Phase 2B evidence adapters."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from .db_models import CustomerRiskProfileRecord, LoanRecord
from .mbl_scorecard import calculate
from .phase1_customer import record_customer_event
from .phase2b_data_adapters import build_phase2b_inputs


def build_assessment_input(db: Session, customer_id: int, loan: LoanRecord | None = None) -> dict[str, Any]:
    """Backward-compatible assessment payload enriched with provenance."""
    payload = build_phase2b_inputs(db, customer_id)
    result = dict(payload["inputs"])
    result["data_quality"] = payload["data_quality"]
    result["geo"] = payload["geo"]
    return result


def _unknown_hard_rejects(hard_rejects: list[str], unavailable: set[str]) -> list[str]:
    """Remove policy hard-stops that were generated only because evidence is absent."""
    field_map = {
        "cibil_enquiries_above_5": "cibil_unsecured_enquiries_30d",
        "cibil_adverse_event_last_3y": "cibil_adverse_last_3y",
        "business_vintage_below_6_months": "business_vintage_years",
        "no_positive_trade_validation": "trade_validations",
        "active_dpd_or_overdue": "active_dpd_overdue",
        "writeoff_last_3y": "writeoff_last_3y",
        "settlement_last_3y": "settlement_last_3y",
        "suit_filed_last_5y": "suit_filed_last_5y",
        "stock_market_transactions_above_policy_limit": "stock_market_transactions_3m",
        "business_address_geo_verification_missing": "business_address_geo_verified",
        "residence_address_geo_verification_missing": "residence_address_geo_verified",
    }
    return [h for h in hard_rejects if field_map.get(h) not in unavailable]


def fraud_screen(i: dict[str, Any]) -> dict[str, Any]:
    flags: list[str] = []
    if i.get("duplicate_customer_ids"): flags.append("POTENTIAL_DUPLICATE_CUSTOMER")
    if i.get("gaming_transactions_3m") is True: flags.append("GAMING_TRANSACTIONS")
    if i.get("stock_market_transactions_3m") is not None and float(i.get("stock_market_transactions_3m") or 0) > 10:
        flags.append("HIGH_STOCK_MARKET_ACTIVITY")
    if i.get("business_address_geo_verified") is False: flags.append("BUSINESS_GEO_NOT_VERIFIED")
    if i.get("residence_address_geo_verified") is False: flags.append("RESIDENCE_GEO_NOT_VERIFIED")
    if i.get("kyc_verified") is False: flags.append("KYC_NOT_VERIFIED")
    if i.get("primary_bank_verified") is False: flags.append("PRIMARY_BANK_NOT_VERIFIED")
    return {"status": "REVIEW" if flags else "CLEAR", "flags": flags, "flag_count": len(flags)}


def assess(db: Session, customer_id: int, loan_id: int | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    loan = db.get(LoanRecord, loan_id) if loan_id else db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).first()
    if not loan:
        raise ValueError("loan_request_not_found")
    if loan.customer_id != customer_id:
        raise ValueError("loan_customer_mismatch")

    payload = build_phase2b_inputs(db, customer_id)
    inputs = dict(payload["inputs"])
    quality = dict(payload["data_quality"])
    unavailable = set(quality.get("unavailable_fields", []))
    if overrides:
        inputs.update(overrides)
        unavailable -= set(overrides.keys())
        quality["override_fields"] = sorted(overrides.keys())
    quality["unavailable_fields"] = sorted(unavailable)
    quality["manual_review_required"] = bool(unavailable)

    fraud = fraud_screen(inputs)
    score_result = calculate(inputs)
    hard = _unknown_hard_rejects(list(score_result.hard_rejects), unavailable)

    # Missing evidence must never be converted into an automatic rejection.
    # Actual policy hard-stops (for example a confirmed gaming transaction or
    # confirmed 90+ DPD/write-off) remain hard rejects.
    actual_hard = list(hard)
    if fraud["status"] == "REVIEW" and "fraud_review_required" not in actual_hard:
        actual_hard.append("fraud_review_required")

    if any(h != "fraud_review_required" for h in hard):
        decision, approval = "REJECT", 0
    elif quality["manual_review_required"] or fraud["status"] == "REVIEW":
        decision, approval = "MANUAL_REVIEW", 0
    elif score_result.decision == "REJECT":
        decision, approval = "REJECT", 0
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
    reasons = list(score_result.reasons)
    if quality["manual_review_required"]:
        reasons.append("missing_or_unverified_evidence_requires_manual_review")
    reasons.extend(fraud["flags"])
    loan.scorecard_reasons = json.dumps(list(dict.fromkeys(reasons)), ensure_ascii=False)
    loan.scorecard_hard_rejects = json.dumps(list(dict.fromkeys(actual_hard)), ensure_ascii=False)
    loan.scorecard_factor_scores = json.dumps(score_result.factor_scores, ensure_ascii=False)

    risk = db.query(CustomerRiskProfileRecord).filter(CustomerRiskProfileRecord.customer_id == customer_id).first()
    if not risk:
        risk = CustomerRiskProfileRecord(customer_id=customer_id)
        db.add(risk)
    risk.risk_status = "high" if decision == "REJECT" else "review" if decision == "MANUAL_REVIEW" else "assessed"
    risk.fraud_status = fraud["status"].lower()
    risk.credit_status = decision.lower()
    risk.risk_grade = "H" if decision == "REJECT" else "M" if decision == "MANUAL_REVIEW" else "L"
    risk.risk_flags = json.dumps(fraud["flags"], ensure_ascii=False)
    risk.last_assessed_at = datetime.now(timezone.utc)

    record_customer_event(
        db,
        customer_id,
        "CREDIT_ASSESSMENT_COMPLETED",
        details={
            "loan_id": loan.id,
            "decision": decision,
            "score": score_result.score,
            "fraud_status": fraud["status"],
            "data_readiness_percent": quality.get("readiness_percent"),
            "manual_review_required": quality["manual_review_required"],
        },
    )
    db.commit()
    db.refresh(loan)
    db.refresh(risk)

    return {
        "loan_id": loan.id,
        "customer_id": customer_id,
        "inputs": inputs,
        "data_quality": quality,
        "credit": score_result.payload() | {
            "decision": decision,
            "approval_percent": approval,
            "eligible_amount": loan.eligible_amount,
        },
        "fraud": fraud,
        "risk_profile": {
            "risk_grade": risk.risk_grade,
            "risk_status": risk.risk_status,
            "fraud_status": risk.fraud_status,
            "credit_status": risk.credit_status,
        },
    }
