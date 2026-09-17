"""Phase 2O - Loan Resolution, Closure & NOC readiness.

Deterministic post-collection resolution controls. This module evaluates whether a
loan is ready for closure/NOC or requires an unresolved operational action. It
does not waive balances, approve settlements, or post payments.
"""
from dataclasses import dataclass

PHASE2O_VERSION = "MBL-RESOLUTION-2O-v1"

RESOLUTION_STATES = ("OPEN", "SETTLEMENT_PENDING", "SETTLEMENT_APPROVED", "READY_FOR_CLOSURE", "CLOSED")
BLOCKERS = (
    "OUTSTANDING_BALANCE",
    "UNALLOCATED_REPAYMENT",
    "PENDING_SETTLEMENT",
    "APPROVED_SETTLEMENT_UNPAID",
    "PENDING_OPERATION",
)

@dataclass(frozen=True)
class ResolutionAssessment:
    loan_id: int
    state: str
    closure_ready: bool
    outstanding_amount: float
    blockers: tuple[str, ...]
    resolution_action: str


def assess_resolution(*, loan_id: int, outstanding_amount: float,
                       repayment_unallocated: float = 0.0,
                       settlement_status: str | None = None,
                       settlement_approved_amount: float = 0.0,
                       settlement_paid_amount: float = 0.0,
                       pending_operations: int = 0,
                       loan_status: str = "") -> ResolutionAssessment:
    outstanding = round(max(0.0, float(outstanding_amount or 0)), 2)
    unallocated = round(max(0.0, float(repayment_unallocated or 0)), 2)
    status = str(settlement_status or "").lower()
    blockers = []
    if outstanding > 0: blockers.append("OUTSTANDING_BALANCE")
    if unallocated > 0: blockers.append("UNALLOCATED_REPAYMENT")
    if status == "quoted": blockers.append("PENDING_SETTLEMENT")
    if status == "approved" and settlement_paid_amount < settlement_approved_amount:
        blockers.append("APPROVED_SETTLEMENT_UNPAID")
    if int(pending_operations or 0) > 0: blockers.append("PENDING_OPERATION")

    if str(loan_status).lower() == "closed" and not blockers:
        state = "CLOSED"
    elif status == "approved" and "APPROVED_SETTLEMENT_UNPAID" in blockers:
        state = "SETTLEMENT_APPROVED"
    elif status == "quoted":
        state = "SETTLEMENT_PENDING"
    elif not blockers:
        state = "READY_FOR_CLOSURE"
    else:
        state = "OPEN"

    if state == "READY_FOR_CLOSURE": action = "CLOSE_AND_ISSUE_NOC"
    elif state == "SETTLEMENT_APPROVED": action = "COLLECT_APPROVED_SETTLEMENT"
    elif state == "SETTLEMENT_PENDING": action = "SETTLEMENT_REVIEW"
    else: action = "RESOLVE_BLOCKERS"
    return ResolutionAssessment(loan_id, state, not blockers, outstanding, tuple(blockers), action)


def resolution_contract():
    return {
        "version": PHASE2O_VERSION,
        "purpose": "loan resolution, closure readiness and NOC governance",
        "states": list(RESOLUTION_STATES),
        "blockers": list(BLOCKERS),
        "principles": [
            "deterministic and explainable",
            "no automatic waiver or settlement approval",
            "no payment posting",
            "closure requires zero outstanding balance and no unresolved blockers",
            "settlement completion must be evidenced before closure",
            "operational resolution only; no credit decision",
        ],
    }
