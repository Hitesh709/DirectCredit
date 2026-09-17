"""Phase 2Q - Accounting & General Ledger Controls.

Provides deterministic accounting posting contracts and ledger-balance
validation around the existing accounting_ledger model. This layer never
silently changes a loan balance and rejects unbalanced journal entries.
"""
from dataclasses import dataclass

PHASE2Q_VERSION = "MBL-ACCOUNTING-2Q-v1"

@dataclass(frozen=True)
class JournalValidation:
    status: str
    debit: float
    credit: float
    variance: float
    reason: str


def validate_journal(*, debit: float, credit: float, tolerance: float = 0.01) -> JournalValidation:
    d = round(max(0.0, float(debit or 0)), 2)
    c = round(max(0.0, float(credit or 0)), 2)
    variance = round(d - c, 2)
    if d <= 0 and c <= 0:
        return JournalValidation("REJECTED", d, c, variance, "EMPTY_JOURNAL")
    if abs(variance) > max(0.0, float(tolerance)):
        return JournalValidation("REJECTED", d, c, variance, "UNBALANCED_JOURNAL")
    return JournalValidation("VALID", d, c, variance, "BALANCED")


def ledger_summary(entries: list[dict]) -> dict:
    debit = round(sum(max(0.0, float(e.get("debit") or 0)) for e in entries or []), 2)
    credit = round(sum(max(0.0, float(e.get("credit") or 0)) for e in entries or []), 2)
    return {"entry_count": len(entries or []), "total_debit": debit, "total_credit": credit,
            "balance": round(debit - credit, 2), "status": "BALANCED" if round(debit-credit,2) == 0 else "OUT_OF_BALANCE"}


def accounting_contract():
    return {
        "version": PHASE2Q_VERSION,
        "purpose": "general ledger posting controls and accounting integrity",
        "journal_rule": "total_debit == total_credit within explicit tolerance",
        "principles": [
            "balanced double-entry journals only",
            "no silent balance mutation",
            "idempotent reference required for production posting",
            "accounting evidence must remain auditable",
            "reconciliation exceptions require review before closure",
        ],
    }
