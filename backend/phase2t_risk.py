"""Phase 2T - Advanced Credit Risk Engine.

Deterministic risk analytics built on verified/evidence-backed inputs. This layer
does not claim a statistically validated PD/LGD model; it provides transparent
risk grading and expected-loss calculations once calibrated parameters are supplied.
"""
from dataclasses import dataclass
from typing import Any, Dict

PHASE2T_VERSION = "MBL-CREDIT-RISK-2T-v1"
RISK_GRADES = ("A", "B", "C", "D", "E")

@dataclass(frozen=True)
class RiskResult:
    risk_grade: str
    risk_score: int
    pd: float
    lgd: float
    ead: float
    expected_loss: float
    reasons: list[str]
    model_status: str

def _num(v: Any, default: float = 0.0) -> float:
    try: return float(v)
    except (TypeError, ValueError): return default

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def calculate_risk(*, scorecard_score: Any = 0, scorecard_max: Any = 125,
                   foir: Any = 0, cibil_score: Any = 0,
                   bank_bounces_3m: Any = 0, ecs_returns_12m: Any = 0,
                   business_vintage_years: Any = 0, active_dpd: bool = False,
                   fraud_score: Any = 0, overdue_amount: Any = 0,
                   sanctioned_amount: Any = 0, outstanding_amount: Any = 0,
                   pd_override: Any = None, lgd_override: Any = None,
                   ead_override: Any = None) -> Dict[str, Any]:
    score = _num(scorecard_score)
    max_score = max(1.0, _num(scorecard_max, 125))
    normalized = _clamp(score / max_score * 100, 0, 100)
    risk_score = round(normalized)
    reasons: list[str] = []

    if active_dpd:
        risk_score -= 25; reasons.append("active_dpd")
    if _num(fraud_score) >= 60:
        risk_score -= 25; reasons.append("high_fraud_signal")
    elif _num(fraud_score) >= 20:
        risk_score -= 10; reasons.append("fraud_review_signal")
    if _num(foir) > 1: foir_n = _num(foir) / 100
    else: foir_n = _num(foir)
    if foir_n > .65: risk_score -= 15; reasons.append("high_foir")
    elif foir_n > .50: risk_score -= 8; reasons.append("elevated_foir")
    if _num(cibil_score) and _num(cibil_score) < 650:
        risk_score -= 15; reasons.append("lower_bureau_score")
    elif _num(cibil_score) and _num(cibil_score) < 700:
        risk_score -= 7; reasons.append("moderate_bureau_score")
    if _num(bank_bounces_3m) >= 2: risk_score -= 12; reasons.append("bank_bounces")
    elif _num(bank_bounces_3m) == 1: risk_score -= 5; reasons.append("bank_bounce")
    if _num(ecs_returns_12m) >= 2: risk_score -= 12; reasons.append("ecs_returns")
    if _num(business_vintage_years) < .5: risk_score -= 20; reasons.append("short_business_vintage")
    elif _num(business_vintage_years) < 1: risk_score -= 8; reasons.append("limited_business_vintage")
    risk_score = round(_clamp(risk_score, 0, 100))

    if risk_score >= 85: grade = "A"
    elif risk_score >= 70: grade = "B"
    elif risk_score >= 55: grade = "C"
    elif risk_score >= 40: grade = "D"
    else: grade = "E"

    # Transparent baseline estimates, explicitly marked as uncalibrated.
    baseline_pd = {"A": .02, "B": .05, "C": .10, "D": .20, "E": .35}[grade]
    pd = _clamp(_num(pd_override, baseline_pd), 0, 1)
    lgd = _clamp(_num(lgd_override, .45), 0, 1)
    ead = max(0.0, _num(ead_override, _num(outstanding_amount, _num(sanctioned_amount))))
    expected_loss = round(ead * pd * lgd, 2)
    return RiskResult(grade, risk_score, pd, lgd, ead, expected_loss,
                      list(dict.fromkeys(reasons)),
                      "CALIBRATION_REQUIRED" if pd_override is None or lgd_override is None else "PARAMETERS_SUPPLIED").__dict__

def risk_contract() -> Dict[str, Any]:
    return {
        "version": PHASE2T_VERSION,
        "purpose": "Advanced, explainable credit-risk grading and expected-loss framework",
        "risk_grades": list(RISK_GRADES),
        "outputs": ["risk_grade", "risk_score", "PD", "LGD", "EAD", "expected_loss"],
        "rules": [
            "Baseline PD/LGD parameters are placeholders until calibrated and validated on portfolio outcomes",
            "This engine does not independently approve or reject a loan",
            "Overrides must be controlled, versioned, and auditable",
            "Expected loss = EAD × PD × LGD",
        ],
    }
