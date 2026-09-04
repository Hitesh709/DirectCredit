"""Canonical MBL eligibility and decision engine.

All scoring is backend-owned. This module does not fabricate bureau or bank
scores: unavailable inputs remain unavailable and the decision is REFER until
required evidence is present.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

MIN_LOAN = 5_000
MAX_LOAN = 15_000

@dataclass
class EligibilityResult:
    eligible: bool
    requested_amount: int
    eligible_amount: int
    decision: str
    reasons: list[str]
    score: Optional[int]
    score_source: str
    product: str
    tenure_months: Optional[int]
    foir: Optional[float]
    inputs_complete: bool

    def payload(self) -> Dict[str, Any]:
        return asdict(self)

def validate_request(amount: int, tenure_months: int) -> list[str]:
    reasons = []
    if amount < MIN_LOAN or amount > MAX_LOAN:
        reasons.append("requested_amount_outside_mbl_range")
    if tenure_months <= 0 or tenure_months > 36:
        reasons.append("invalid_tenure")
    return reasons

def assess(*, requested_amount: int, tenure_months: int,
           monthly_income: Optional[float] = None,
           existing_emi: Optional[float] = None,
           bureau_score: Optional[float] = None,
           banking_score: Optional[float] = None,
           score: Optional[int] = None,
           score_source: str = "scorecard_not_configured") -> EligibilityResult:
    reasons = validate_request(requested_amount, tenure_months)
    foir = None
    if monthly_income and monthly_income > 0 and existing_emi is not None:
        foir = round(float(existing_emi) / float(monthly_income), 4)
        if foir > 0.50:
            reasons.append("foir_above_policy_limit")
    required_external_inputs = bureau_score is not None and banking_score is not None
    inputs_complete = required_external_inputs and monthly_income is not None
    eligible_amount = max(0, min(MAX_LOAN, requested_amount)) if not reasons else 0
    if not inputs_complete:
        decision = "REFER"
        reasons.append("required_assessment_inputs_unavailable")
        eligible = False
    elif score is None:
        decision = "REFER"
        reasons.append("official_scorecard_not_configured")
        eligible = False
    elif score >= 100 and not reasons:
        decision, eligible = "APPROVE", True
    elif score >= 75 and not reasons:
        decision, eligible = "REFER", False
        reasons.append("manual_review_required")
    else:
        decision, eligible = "DECLINE", False
        reasons.append("score_below_policy_threshold")
    return EligibilityResult(eligible, requested_amount, eligible_amount, decision,
                             list(dict.fromkeys(reasons)), score, score_source,
                             "MBL", tenure_months, foir, inputs_complete)
