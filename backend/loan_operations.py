"""Canonical operation contracts consumed by Admin UI/API.

These helpers only operate on persisted records. Privileged state changes should
be performed by an authenticated admin/operations principal in the API layer.
"""
from __future__ import annotations
from typing import Any

LOAN_OPERATION_STATUSES = {"draft", "assessment", "sanctioned", "customer_approved", "esign_pending", "esigned", "mandate_pending", "mandate_active", "disbursement_pending", "disbursed", "active", "overdue", "repaid", "closed", "rejected", "cancelled"}

def loan_summary(loan: Any) -> dict:
    return {"loan_id": loan.id, "customer_id": loan.customer_id, "amount": loan.amount, "status": loan.status}

def can_admin_transition(current: str, target: str) -> bool:
    # The canonical lifecycle module remains the source of truth for actual transitions.
    from .loan_lifecycle import can_transition
    return can_transition(current, target)

def operation_payload(loan: Any, operation: str) -> dict:
    return {"operation": operation, "loan": loan_summary(loan), "allowed": operation in {"view", "assess", "sanction", "approve", "esign", "emandate", "disburse"}}
