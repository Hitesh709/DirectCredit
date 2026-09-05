"""Official MBL credit scorecard based on the supplied assessment framework.

The source document states a 125-point maximum, while its listed factor maxima
sum to 130 before the +5 both-owned bonus. We preserve every listed factor,
record the raw total, and cap the published score at the stated 125-point
maximum rather than silently deleting a source factor.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

VERSION = "MBL-125-v1"
MAX_POINTS = 125
AUTO_APPROVAL_MIN = 95

@dataclass
class ScorecardResult:
    score: int
    max_score: int
    version: str
    decision: str
    approval_percent: int
    reasons: list[str]
    hard_rejects: list[str]
    factor_scores: dict[str, int]
    raw_score: int

    def payload(self) -> dict[str, Any]:
        return asdict(self)

def _num(v, default=0.0):
    try: return float(v)
    except (TypeError, ValueError): return default

def _int(v, default=0):
    try: return int(v)
    except (TypeError, ValueError): return default

def _norm(v): return str(v or "").strip().lower().replace(" ", "_")

def calculate(i: dict[str, Any]) -> ScorecardResult:
    s: dict[str,int] = {}; hard: list[str] = []; reasons: list[str] = []
    ownership = _norm(i.get("ownership_proof"))
    s["ownership_proof"] = 5 if ownership == "applicant" else 3 if ownership in {"parent","grandfather","family"} else -5 if ownership == "rented" else 0
    both_owned = bool(i.get("business_owned")) and bool(i.get("residence_owned"))
    geography = _norm(i.get("business_geography"))
    s["business_geography"] = {"tier1":5,"tier2":5,"tier_1":5,"tier_2":5,"tier3":3,"tier_3":3,"rural":1,"high_risk":-5,"high-risk":-5}.get(geography,0)
    age = _int(i.get("age")); s["age"] = 5 if 31<=age<=50 else 3 if 25<=age<=30 or 51<=age<=55 else 1 if 21<=age<=24 or 56<=age<=59 else 0
    enquiries = _int(i.get("cibil_unsecured_enquiries_30d")); s["cibil_enquiries"] = 5 if enquiries<=2 else 3 if enquiries<=5 else -5
    dpd = _norm(i.get("cibil_repayment"))
    if i.get("cibil_adverse_last_3y"):
        s["cibil_repayment"] = 0; hard.append("cibil_adverse_event_last_3y")
    elif dpd in {"none","no_dpd","clean"}: s["cibil_repayment"] = 15
    elif dpd == "no_dpd_3y": s["cibil_repayment"] = 10
    elif dpd == "30dpd_1y": s["cibil_repayment"] = 8
    elif dpd == "31_60dpd_2y": s["cibil_repayment"] = 5
    else: s["cibil_repayment"] = 0
    unsecured = _int(i.get("unsecured_loans_50k_plus")); s["unsecured_track"] = 10 if unsecured>=3 else 7 if unsecured==2 else 5 if unsecured==1 else 0
    credits = _num(i.get("avg_monthly_bank_credits")); s["bank_credits"] = 10 if credits>=500000 else 7 if credits>=300000 else 4 if credits>=150000 else 1 if credits<75000 else 0
    bounces = _int(i.get("bank_bounces_3m")); s["bank_stability"] = 5 if bounces==0 else 3 if bounces==1 else 0
    aqb = _num(i.get("aqb")); s["aqb"] = 5 if aqb>=15000 else 3 if aqb>=10000 else 1 if aqb>=5000 else 0
    ecs = _int(i.get("ecs_returns_12m")); s["emi_track"] = 5 if ecs==0 else 3 if ecs==1 else 0
    business_type = _norm(i.get("business_type")); s["business_type"] = 5 if business_type in {"trader","retail","manufacturing"} else 3 if business_type in {"b2b_service"} else 2 if business_type in {"b2c_service","seasonal","agent","agent_based"} else 0
    vintage = _num(i.get("business_vintage_years")); s["business_vintage"] = 5 if vintage>=3 else 3 if vintage>=1 else 1 if vintage>=0.5 else 0
    stock = _num(i.get("business_stock")); s["business_stock"] = 5 if stock>=500000 else 3 if stock>=300000 else 0
    emi = _num(i.get("monthly_emi_obligation")); s["monthly_emi"] = 5 if emi<30000 else 3 if emi<=40000 else 2 if emi<=50000 else 0
    foir = _num(i.get("foir")); foir = foir/100 if foir>1 else foir; s["foir"] = 5 if foir<=0.40 else 3 if foir<=0.50 else 2 if foir<=0.65 else 0
    trade = _int(i.get("trade_validations")); s["trade_validation"] = 10 if trade>5 else 7 if trade==5 else 5 if trade>=3 else 3 if trade>=1 else 0
    gst_years = _num(i.get("gst_years")); s["gst"] = 5 if gst_years>=3 else 3 if gst_years>=2 else 2 if gst_years>=1 else 1 if gst_years>0 else 0
    turnover = _num(i.get("gstr3b_avg_monthly_turnover")); s["gstr3b"] = 10 if turnover>=500000 else 8 if turnover>=300000 else 5 if turnover>=200000 else 3 if turnover>=76000 else 0
    itr = _num(i.get("itr_income")); s["itr"] = 5 if itr>=500000 else 3 if itr>=300000 else 0
    mobile_years = _num(i.get("mobile_stability_years")); s["mobile_stability"] = 5 if mobile_years>5 else 3 if mobile_years>=3 else 1 if mobile_years>=1 else 0
    if both_owned: s["both_owned_bonus"] = 5

    # Explicit policy requirements from the source framework.
    if enquiries > 5: hard.append("cibil_enquiries_above_5")
    if bounces >= 2: hard.append("bank_bounces_2_plus")
    if ecs >= 2: hard.append("ecs_returns_2_plus")
    if vintage < 0.5: hard.append("business_vintage_below_6_months")
    if trade <= 0: hard.append("no_positive_trade_validation")
    if i.get("active_dpd_overdue"): hard.append("active_dpd_or_overdue")
    if i.get("writeoff_last_3y"): hard.append("writeoff_last_3y")
    if i.get("settlement_last_3y"): hard.append("settlement_last_3y")
    if i.get("suit_filed_last_5y"): hard.append("suit_filed_last_5y")
    if i.get("gaming_transactions_3m"): hard.append("gaming_transactions_present")
    if _int(i.get("stock_market_transactions_3m")) > 10: hard.append("stock_market_transactions_above_policy_limit")
    if i.get("business_address_geo_verified") is False: hard.append("business_address_geo_verification_missing")
    if i.get("residence_address_geo_verified") is False: hard.append("residence_address_geo_verification_missing")

    negative_count=sum(v==-5 for v in s.values()); zero_count=sum(v==0 for v in s.values())
    if negative_count>=2: hard.append("two_negative_5_factors")
    if negative_count>=1 and zero_count>=3: hard.append("three_zero_factors_with_negative_5")

    raw=sum(s.values()); total=max(0,min(MAX_POINTS,raw))
    if raw>MAX_POINTS: reasons.append("raw_score_capped_to_stated_125_maximum")
    if hard:
        decision,pct="REJECT",0; reasons.extend(hard)
    elif total<50: decision,pct="REJECT",0; reasons.append("score_below_50")
    elif total<95: decision,pct="MANUAL_REVIEW",0; reasons.append("score_requires_manual_review")
    elif total<100: decision,pct="APPROVE",80
    elif total<105: decision,pct="APPROVE",90
    else: decision,pct="APPROVE",100
    return ScorecardResult(total,MAX_POINTS,VERSION,decision,pct,list(dict.fromkeys(reasons)),list(dict.fromkeys(hard)),s,raw)
