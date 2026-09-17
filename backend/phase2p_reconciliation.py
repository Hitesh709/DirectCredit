"""Phase 2P - Financial Reconciliation & Exception Control.

Reconciles repayment/collection evidence against the loan ledger without
mutating balances. It produces deterministic exception records for operations
and accounting teams. No automatic payment posting or balance adjustment.
"""
from dataclasses import dataclass

PHASE2P_VERSION = "MBL-RECONCILIATION-2P-v1"

EXCEPTION_TYPES = (
    "PAYMENT_REFERENCE_MISSING",
    "PAYMENT_AMOUNT_MISMATCH",
    "DUPLICATE_PAYMENT_REFERENCE",
    "UNALLOCATED_PAYMENT",
    "COLLECTION_REFERENCE_MISMATCH",
    "SETTLEMENT_EVIDENCE_MISSING",
    "LOAN_BALANCE_MISMATCH",
)

@dataclass(frozen=True)
class ReconciliationResult:
    loan_id: int
    status: str
    expected_amount: float
    observed_amount: float
    variance: float
    exceptions: tuple[str, ...]
    action: str


def _money(value):
    return round(max(0.0, float(value or 0)), 2)


def reconcile_loan(*, loan_id: int, expected_amount: float,
                   observed_amount: float, repayment_references: list[str] | None = None,
                   duplicate_references: int = 0, unallocated_amount: float = 0.0,
                   collection_reference_mismatch: bool = False,
                   settlement_evidence_missing: bool = False,
                   ledger_balance: float | None = None, loan_balance: float | None = None,
                   tolerance: float = 1.0) -> ReconciliationResult:
    expected = _money(expected_amount)
    observed = _money(observed_amount)
    variance = round(observed - expected, 2)
    exceptions = []
    refs = [str(x).strip() for x in (repayment_references or []) if str(x).strip()]
    if observed > 0 and not refs:
        exceptions.append("PAYMENT_REFERENCE_MISSING")
    if abs(variance) > max(0.0, float(tolerance)):
        exceptions.append("PAYMENT_AMOUNT_MISMATCH")
    if int(duplicate_references or 0) > 0:
        exceptions.append("DUPLICATE_PAYMENT_REFERENCE")
    if _money(unallocated_amount) > 0:
        exceptions.append("UNALLOCATED_PAYMENT")
    if collection_reference_mismatch:
        exceptions.append("COLLECTION_REFERENCE_MISMATCH")
    if settlement_evidence_missing:
        exceptions.append("SETTLEMENT_EVIDENCE_MISSING")
    if ledger_balance is not None and loan_balance is not None:
        if abs(float(ledger_balance) - float(loan_balance)) > max(0.0, float(tolerance)):
            exceptions.append("LOAN_BALANCE_MISMATCH")
    status = "RECONCILED" if not exceptions else "EXCEPTION"
    action = "NO_ACTION" if status == "RECONCILED" else "ACCOUNTING_REVIEW"
    return ReconciliationResult(loan_id, status, expected, observed, variance, tuple(exceptions), action)


def reconciliation_contract():
    return {
        "version": PHASE2P_VERSION,
        "purpose": "financial reconciliation and exception control",
        "exception_types": list(EXCEPTION_TYPES),
        "principles": [
            "read-only reconciliation evidence",
            "no automatic balance mutation",
            "no automatic payment posting",
            "deterministic exception classification",
            "audit and accounting review required for exceptions",
            "monetary comparisons use an explicit tolerance",
        ],
    }
