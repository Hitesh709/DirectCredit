"""Phase 2D: deterministic policy orchestration and decision contract.

This layer sits between evidence-backed inputs and the MBL scorecard. It keeps
policy rules explicit, versioned, explainable, and conservative around unknown
evidence. Missing evidence routes to manual review; it is never silently
converted into a rejection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

POLICY_VERSION = "MBL-POLICY-2D-v1"

@dataclass(frozen=True)
class PolicyResult:
    decision: str
    approval_percent: int
    eligible_amount: int
    reasons: list[str]
    hard_rejects: list[str]
    review_reasons: list[str]
    policy_version: str = POLICY_VERSION

    def payload(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "approval_percent": self.approval_percent,
            "eligible_amount": self.eligible_amount,
            "reasons": self.reasons,
            "hard_rejects": self.hard_rejects,
            "review_reasons": self.review_reasons,
            "policy_version": self.policy_version,
        }


def _bool(v: Any) -> bool | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"true", "yes", "1", "verified", "clean"}


def evaluate_policy(*, score: float, score_decision: str, score_approval_percent: int,
                    requested_amount: float, unavailable_fields: list[str] | set[str] | None = None,
                    fraud_status: str = "CLEAR", fraud_flags: list[str] | None = None,
                    hard_rejects: list[str] | None = None, inputs: dict[str, Any] | None = None) -> PolicyResult:
    inputs = inputs or {}
    unavailable = set(unavailable_fields or [])
    hard = list(dict.fromkeys(hard_rejects or []))
    fraud_flags = list(dict.fromkeys(fraud_flags or []))
    reasons: list[str] = []
    review: list[str] = []

    # Explicit evidence-based policy stops.
    if fraud_status == "REVIEW" and fraud_flags:
        review.append("fraud_review_required")
    for field, reason in (
        ("active_dpd_overdue", "active_dpd_or_overdue"),
        ("writeoff_last_3y", "writeoff_last_3y"),
        ("settlement_last_3y", "settlement_last_3y"),
        ("suit_filed_last_5y", "suit_filed_last_5y"),
    ):
        value = _bool(inputs.get(field))
        if value is True:
            hard.append(reason)

    # A known failed verification is a review/reject input depending on policy;
    # 2D keeps it in manual review unless a scorecard hard-stop is explicit.
    for field, label in (("kyc_verified", "kyc_not_verified"), ("primary_bank_verified", "primary_bank_not_verified")):
        value = _bool(inputs.get(field))
        if value is False:
            review.append(label)

    if unavailable:
        review.append("missing_or_unverified_evidence")
        reasons.append(f"data_completeness_{max(0, 100 - min(100, len(unavailable) * 5))}")

    hard = list(dict.fromkeys(hard))
    review = list(dict.fromkeys(review))
    reasons.extend(fraud_flags)

    if hard:
        decision, approval = "REJECT", 0
    elif review:
        decision, approval = "MANUAL_REVIEW", 0
    elif str(score_decision).upper() == "REJECT":
        decision, approval = "REJECT", 0
    else:
        decision = str(score_decision).upper()
        approval = int(score_approval_percent or 0)

    eligible = 0 if approval <= 0 else int(round(float(requested_amount or 0) * approval / 100))
    return PolicyResult(decision, approval, eligible, list(dict.fromkeys(reasons)), hard, review)


def policy_contract() -> dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION,
        "decision_states": ["APPROVE", "MANUAL_REVIEW", "REJECT"],
        "approval_bands": [
            {"min_score": 105, "approval_percent": 100},
            {"min_score": 100, "approval_percent": 90},
            {"min_score": 95, "approval_percent": 80},
            {"min_score": 50, "decision": "MANUAL_REVIEW"},
            {"min_score": 0, "decision": "REJECT"},
        ],
        "principles": [
            "unknown evidence does not become a negative fact",
            "confirmed hard stops remain hard stops",
            "every decision carries policy version and reasons",
        ],
    }
