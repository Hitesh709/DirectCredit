"""Official MBL credit scorecard.

The source framework contains 18 scored factors totalling 120 base points,
plus a 5-point "both owned" bonus, giving the stated 125-point maximum.
Hard policy rejects are kept separate from the score and always override it.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

VERSION = "MBL-125-v1"
BASE_MAX_POINTS = 120
BONUS_MAX_POINTS = 5
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

    def payload(self) -> dict[str, Any]:
        return asdict(self)

def _num(v, default=0.0):
    try: return float(v)
    except (TypeError, ValueError): return default

def _int(v, default=0):
    try: return int(v)
    except (TypeError, ValueError): return default

def _norm(v): return str(v or "").strip().lower()

def calculate(i: dict[str, Any]) -> ScorecardResult:
    s: dict[str,int] = {}
    hard: list[str] = []
    reasons: list[str] = []

    ownership = _norm(i.get("ownership_proof"))
    s["ownership_proof"] = 5 if ownership == "applicant" else 3 if ownership in {"parent","grandfather","family"} else -5 if ownership == "rented" else 0
    both_owned = bool(i.get("business_owned")) and bool(i.get("residence_owned"))

    geography = _norm(i.get("business_geography"))
    s["business_geography"] = {"tier1":5,"tier2":5,"tier_1":5,"tier_2":5,"tier3":3,"tier_3":3,"rural":1,"high_risk":-5,"high-risk":-5}.get(geography,0)
    age = _int(i.get("age"))
    s["age"] = 5 if 31<=age<=50 else 3 if 25<=age<=30 or 51<=age<=55 else 1 if 21<=age<=24 or 56<=age<=59 else 0

    enquiries = _int(i.get("cibil_unsecured_enquiries_30d"))
    s["cibil_enquiries"] = 5 if enquiries<=2 else 3 if enquiries<=5 else -5
    if enquiries > 5: hard.append("cibil_enquiries_above_5")

    dpd = _norm(i.get("cibil_repayment"))
    if i.get("cibil_adverse_last_3y"):
        hard.append("cibil_adverse_event_last_3y")
        s["cibil_repayment"] = 0
    elif dpd in {"none", "no_dpd", "clean"}: s["cibil_repayment"] = 15
    elif dpd == "no_dpd_3y": s["cibil_repayment"] = 10
    elif dpd == "30dpd_1y": s["cibil_repayment"] = 8
    elif dpd == "31_60dpd_2y": s["cibil_repayment"] = 5
    elif dpd == "90dpd_3y": s["cibil_repayment"] = 0
    else: s["cibil_repayment"] = 0

    unsecured = _int(i.get("unsecured_loans_50k_plus"))
    s["unsecured_track"] = 10 if unsecured>=3 else 7 if unsecured==2 else 5 if unsecured==1 else 0

    credits = _num(i.get("avg_monthly_bank_credits"))
    s["bank_credits"] = 10 if credits>=500000 else 7 if credits>=300000 else 4 if credits>=150000 else 1 if credits<75000 else 0
    bounces = _int(i.get("bank_bounces_3m"))
    s["bank_stability"] = 5 if bounces==0 else 3 if bounces==1 else 0
    if bounces>=2: hard.append("bank_bounces_2_plus")

    aqb = _num(i.get("aqb"))
    s["aqb"] = 5 if aqb>=15000 else 3 if aqb>=10000 else 1 if aqb>=5000 else 0
    ecs = _int(i.get("ecs_returns_12m"))
    s["emi_track"] = 5 if ecs==0 else 3 if ecs==1 else 0
    if ecs>=2: hard.append("ecs_returns_2_plus")

    business_type = _norm(i.get("business_type"))
    s["business_type"] = 5 if business_type in {"trader","retail","manufacturing"} else 3 if business_type in {"b2b_service","b2b service"} else 2 if business_type in {"b2c_service","b2c service","seasonal","agent","agent_based"} else 0
    vintage = _num(i.get("business_vintage_years"))
    s["business_vintage"] = 5 if vintage>=3 else 3 if vintage>=1 else 1 if vintage>=0.5 else 0
    if vintage < 0.5: hard.append("business_vintage_below_6_months")

    stock = _num(i.get("business_stock"))
    s["business_stock"] = 5 if stock>=500000 else 3 if stock>=300000 else 0
    emi = _num(i.get("monthly_emi_obligation"))
    s["monthly_emi"] = 5 if emi<30000 else 3 if emi<=40000 else 2 if emi<=50000 else 0
    foir = _num(i.get("foir"))
    s["foir"] = 5 if foir<=0.40 else 3 if foir<=0.50 else 2 if foir<=0.65 else 0

    trade = _int(i.get("trade_validations"))
    s["trade_validation"] = 10 if trade>5 else 7 if trade==5 else 5 if trade>=3 else 3 if trade>=1 else 0
    if trade<=0: hard.append("no_positive_trade_validation")

    gst_years = _num(i.get("gst_years"))
    s["gst"] = 5 if gst_years>=3 else 3 if gst_years>=2 else 2 if gst_years>=1 else 1 if gst_years>0 else 0
    turnover = _num(i.get("gstr3b_avg_monthly_turnover"))
    s["gstr3b"] = 10 if turnover>=500000 else 8 if turnover>=300000 else 5 if turnover>=200000 else 3 if turnover>=76000 else 0
    itr = _num(i.get("itr_income"))
    s["itr"] = 5 if itr>=500000 else 3 if itr>=300000 else 0
    mobile_years = _num(i.get("mobile_stability_years"))
    s["mobile_stability"] = 5 if mobile_years>5 else 3 if mobile_years>=3 else 1 if mobile_years>=1 else 0

    bonus = 5 if both_owned else 0
    if both_owned: s["both_owned_bonus"] = bonus
    total = max(0, sum(s.values()))
    if hard:
        decision, pct = "REJECT", 0
        reasons.extend(hard)
    elif total < 50:
        decision, pct = "REJECT", 0
        reasons.append("score_below_50")
    elif total < 95:
        decision, pct = "MANUAL_REVIEW", 0
        reasons.append("score_requires_manual_review")
    elif total < 100:
        decision, pct = "APPROVE", 80
    elif total < 105:
        decision, pct = "APPROVE", 90
    else:
        decision, pct = "APPROVE", 100
    return ScorecardResult(total, MAX_POINTS, VERSION, decision, pct, list(dict.fromkeys(reasons)), list(dict.fromkeys(hard)), s)
