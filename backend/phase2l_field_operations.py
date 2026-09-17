"""Phase 2L collection-agent and field-operations intelligence.

Operational workflow contracts only. This module never posts payments and does
not make credit decisions.
"""
from dataclasses import dataclass
from datetime import datetime

PHASE2L_VERSION = "MBL-COLLECTION-2L-v1"
VISIT_OUTCOMES = ("CONTACTED", "PROMISE_TO_PAY", "PAYMENT_PROMISED", "NOT_AVAILABLE", "ADDRESS_NOT_FOUND", "REFUSED", "ESCALATED")
CALL_DISPOSITIONS = ("CONNECTED", "NO_ANSWER", "BUSY", "WRONG_NUMBER", "PROMISE_TO_PAY", "REFUSED", "CALL_BACK")

@dataclass(frozen=True)
class Assignment:
    loan_id: int
    customer_id: int
    agent_id: int
    priority_score: int
    reason: str


def assignment_reason(priority_score, urgency):
    if str(urgency).upper() == "CRITICAL": return "critical_collection_priority"
    if int(priority_score) >= 60: return "high_collection_priority"
    return "standard_collection_queue"


def field_operations_contract():
    return {
        "version": PHASE2L_VERSION,
        "roles": ["COLLECTION_AGENT", "FIELD_AGENT", "SUPERVISOR"],
        "call_dispositions": list(CALL_DISPOSITIONS),
        "visit_outcomes": list(VISIT_OUTCOMES),
        "rules": {
            "payment_posting_requires_provider_or_receipt_flow": True,
            "every_call_and_visit_is_audited": True,
            "customer_scope_is_enforced": True,
            "assignment_is_operational_not_credit_decision": True,
            "geo_evidence_is_optional_until_provider_configured": True,
        },
    }

def normalize_disposition(value):
    value=str(value or "").strip().upper()
    if value not in CALL_DISPOSITIONS: raise ValueError("unsupported_call_disposition")
    return value

def normalize_visit_outcome(value):
    value=str(value or "").strip().upper()
    if value not in VISIT_OUTCOMES: raise ValueError("unsupported_visit_outcome")
    return value
