"""Phase 2B data adapters: turn stored evidence into scorecard-ready inputs.

The adapter is deliberately conservative: it never invents bureau, GST, ITR,
trade-validation, or historical mobile data. Unknown evidence is reported as
unavailable so the decision layer can require manual review instead of treating
missing data as a negative event.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from .db_models import (
    BankTransactionRecord,
    CustomerAddressRecord,
    CustomerBankAccountRecord,
    CustomerBusinessRecord,
    CustomerKYCRecord,
    CustomerRecord,
)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _direction(value: Any) -> str:
    return str(value or "").strip().lower()


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value)[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _months_between(latest: datetime, earliest: datetime) -> int:
    return max(1, (latest.year - earliest.year) * 12 + latest.month - earliest.month + 1)


def _keyword(text: Any, words: tuple[str, ...]) -> bool:
    value = str(text or "").lower()
    return any(word in value for word in words)


def bank_statement_intelligence(transactions: list[BankTransactionRecord]) -> dict[str, Any]:
    """Derive conservative banking metrics from transaction rows only."""
    parsed = [(x, _parse_date(x.transaction_date)) for x in transactions]
    dated = [(x, d) for x, d in parsed if d is not None]
    if not dated:
        return {
            "available": False,
            "transaction_count": len(transactions),
            "coverage_months": 0,
            "coverage_start": None,
            "coverage_end": None,
            "avg_monthly_credits": None,
            "avg_monthly_debits": None,
            "aqb": None,
            "bank_bounces_3m": None,
            "ecs_returns_12m": None,
            "gaming_transactions_3m": None,
            "stock_market_transactions_3m": None,
            "monthly_credit_totals": {},
        }

    dated.sort(key=lambda item: item[1])
    start, end = dated[0][1], dated[-1][1]
    coverage_months = _months_between(end, start)
    monthly_credits: dict[str, float] = defaultdict(float)
    monthly_debits: dict[str, float] = defaultdict(float)
    aqb_values: list[float] = []
    bounce_count = 0
    ecs_count = 0
    gaming_count = 0
    stock_count = 0
    last_3m = end - timedelta(days=92)
    last_12m = end - timedelta(days=366)

    for tx, date in dated:
        month = date.strftime("%Y-%m")
        amount = abs(_num(tx.amount))
        direction = _direction(tx.direction)
        if direction in {"credit", "cr", "in", "inflow"}:
            monthly_credits[month] += amount
        elif direction in {"debit", "dr", "out", "outflow"}:
            monthly_debits[month] += amount
        if tx.balance is not None:
            aqb_values.append(_num(tx.balance))

        description = f"{tx.description or ''} {tx.category or ''} {tx.reference or ''}".lower()
        is_return = _keyword(description, ("bounce", "returned", "return", "dishonour", "dishonor"))
        is_ecs = _keyword(description, ("ecs", "nach", "auto debit", "autodebit", "mandate"))
        if is_return and date >= last_3m:
            bounce_count += 1
        if is_return and is_ecs and date >= last_12m:
            ecs_count += 1
        if date >= last_3m and _keyword(description, ("gambl", "casino", "betting", "wager")):
            gaming_count += 1
        if date >= last_3m and _keyword(description, ("zerodha", "groww", "upstox", "angel one", "sharekhan", "nse", "bse", "mutual fund")):
            stock_count += 1

    credit_months = [v for v in monthly_credits.values()]
    debit_months = [v for v in monthly_debits.values()]
    return {
        "available": True,
        "transaction_count": len(transactions),
        "coverage_months": coverage_months,
        "coverage_start": start.date().isoformat(),
        "coverage_end": end.date().isoformat(),
        "avg_monthly_credits": sum(credit_months) / coverage_months if credit_months else 0.0,
        "avg_monthly_debits": sum(debit_months) / coverage_months if debit_months else 0.0,
        "aqb": sum(aqb_values) / len(aqb_values) if aqb_values else None,
        "bank_bounces_3m": bounce_count,
        "ecs_returns_12m": ecs_count,
        "gaming_transactions_3m": gaming_count,
        "stock_market_transactions_3m": stock_count,
        "monthly_credit_totals": dict(sorted(monthly_credits.items())),
    }


def _geo_status(address: CustomerAddressRecord | None) -> tuple[bool | None, str]:
    if not address:
        return None, "not_available"
    status = str(address.verification_status or "").lower()
    if status in {"verified", "success", "completed"} and address.latitude is not None and address.longitude is not None:
        return True, "verified"
    if status in {"rejected", "failed", "invalid"}:
        return False, status
    return None, status or "pending"


def build_phase2b_inputs(db: Session, customer_id: int) -> dict[str, Any]:
    """Build evidence-backed scorecard inputs plus data provenance/readiness."""
    customer = db.get(CustomerRecord, customer_id)
    if not customer:
        raise ValueError("customer_not_found")
    business = db.query(CustomerBusinessRecord).filter(CustomerBusinessRecord.customer_id == customer_id).order_by(CustomerBusinessRecord.id.desc()).first()
    kyc = db.query(CustomerKYCRecord).filter(CustomerKYCRecord.customer_id == customer_id).first()
    primary_bank = db.query(CustomerBankAccountRecord).filter(
        CustomerBankAccountRecord.customer_id == customer_id,
        CustomerBankAccountRecord.is_primary.is_(True),
    ).first()
    addresses = db.query(CustomerAddressRecord).filter(CustomerAddressRecord.customer_id == customer_id).all()
    tx = db.query(BankTransactionRecord).filter(BankTransactionRecord.customer_id == customer_id).order_by(BankTransactionRecord.id.asc()).all()
    bank = bank_statement_intelligence(tx)

    business_address = next((a for a in addresses if str(a.address_type).lower() in {"business", "office", "work"}), None)
    residence_address = next((a for a in addresses if str(a.address_type).lower() in {"residence", "current", "home"}), None)
    business_geo, business_geo_status = _geo_status(business_address)
    residence_geo, residence_geo_status = _geo_status(residence_address)

    cibil_available = _num(customer.cibil_score) > 0
    gst_available = bool(business and business.gstin)
    # A GSTIN proves that a GST identifier is stored; it does not prove GST vintage.
    itr_available = False
    trade_available = False
    mobile_history_available = False

    values: dict[str, Any] = {
        "ownership_proof": customer.residence_ownership or "",
        "business_owned": str(business.ownership_type or "").lower() in {"owned", "own", "applicant"} if business else False,
        "residence_owned": str(customer.residence_ownership or "").lower() in {"owned", "own", "self"},
        "business_geography": "",
        "age": None,
        "cibil_unsecured_enquiries_30d": None,
        "cibil_repayment": "clean" if cibil_available and _num(customer.cibil_score) >= 700 else None,
        "cibil_adverse_last_3y": None,
        "unsecured_loans_50k_plus": None,
        "avg_monthly_bank_credits": bank["avg_monthly_credits"],
        "bank_bounces_3m": bank["bank_bounces_3m"],
        "aqb": bank["aqb"],
        "ecs_returns_12m": bank["ecs_returns_12m"],
        "business_type": business.business_type if business else customer.business_type,
        "business_vintage_years": business.business_vintage_years if business else customer.years_in_business,
        "business_stock": None,
        "monthly_emi_obligation": customer.existing_emi,
        "foir": customer.foir,
        "trade_validations": None,
        "gst_years": None,
        "gstr3b_avg_monthly_turnover": None,
        "itr_income": None,
        "mobile_stability_years": None,
        "active_dpd_overdue": None,
        "writeoff_last_3y": None,
        "settlement_last_3y": None,
        "suit_filed_last_5y": None,
        "gaming_transactions_3m": bool(bank["gaming_transactions_3m"]),
        "stock_market_transactions_3m": bank["stock_market_transactions_3m"],
        "business_address_geo_verified": business_geo,
        "residence_address_geo_verified": residence_geo,
        "monthly_income": customer.monthly_income,
        "existing_emi": customer.existing_emi,
        "bureau_score": customer.cibil_score if cibil_available else None,
        "banking_score": None,
        "primary_bank_verified": bool(primary_bank and str(primary_bank.verification_status).lower() in {"verified", "success", "completed"}),
        "kyc_verified": bool(kyc and str(kyc.status).lower() in {"verified", "completed", "success"}),
        "transaction_count": bank["transaction_count"],
        "credit_transaction_count": sum(1 for x in tx if _direction(x.direction) in {"credit", "cr", "in", "inflow"}),
        "debit_transaction_count": sum(1 for x in tx if _direction(x.direction) in {"debit", "dr", "out", "outflow"}),
    }

    if customer.date_of_birth:
        dob = _parse_date(customer.date_of_birth)
        if dob:
            values["age"] = max(0, int((datetime.utcnow() - dob).days / 365.25))

    unavailable = []
    if not cibil_available:
        unavailable += ["bureau_score", "cibil_repayment", "cibil_unsecured_enquiries_30d", "cibil_adverse_last_3y", "unsecured_loans_50k_plus"]
    else:
        unavailable += ["cibil_unsecured_enquiries_30d", "cibil_adverse_last_3y", "unsecured_loans_50k_plus"]
    if not gst_available:
        unavailable += ["gst_years", "gstr3b_avg_monthly_turnover"]
    else:
        unavailable += ["gst_years", "gstr3b_avg_monthly_turnover"]
    unavailable += ["itr_income", "trade_validations", "mobile_stability_years", "business_stock", "active_dpd_overdue", "writeoff_last_3y", "settlement_last_3y", "suit_filed_last_5y"]
    if values["age"] is None:
        unavailable.append("age")
    if not bank["available"] or bank["coverage_months"] < 3:
        unavailable += ["avg_monthly_bank_credits", "bank_bounces_3m", "aqb", "ecs_returns_12m"]

    known = len(values) - len(set(unavailable))
    total = len(values)
    readiness = round(100 * known / max(total, 1))
    return {
        "customer_id": customer_id,
        "inputs": values,
        "data_quality": {
            "readiness_percent": readiness,
            "bank_statement": bank,
            "sources": {
                "customer_profile": True,
                "business_profile": business is not None,
                "kyc_profile": kyc is not None,
                "primary_bank": primary_bank is not None,
                "bank_transactions": bank["available"],
                "cibil": cibil_available,
                "gst_registration": gst_available,
                "itr": itr_available,
                "trade_validation": trade_available,
                "mobile_history": mobile_history_available,
            },
            "unavailable_fields": sorted(set(unavailable)),
            "manual_review_required": bool(unavailable),
        },
        "geo": {
            "business": {"verified": business_geo, "status": business_geo_status},
            "residence": {"verified": residence_geo, "status": residence_geo_status},
        },
    }
