"""Phase 2K communication orchestration contracts.

Provider-neutral notification planning. This module creates communication
plans/audit records; it does not send messages by itself.
"""
from dataclasses import dataclass
from datetime import date
import os

PHASE2K_VERSION = "MBL-COMMUNICATION-2K-v1"
DEFAULT_DPD_TRIGGERS = (0, 1, 3, 7, 15, 30, 60, 90)
CHANNELS = ("sms", "whatsapp", "email")

@dataclass(frozen=True)
class CommunicationPlan:
    event: str
    template: str
    channels: tuple[str, ...]
    reason: str


def _enabled_channels(preferences=None):
    p = preferences or {}
    channels = []
    if p.get("sms", True): channels.append("sms")
    if p.get("whatsapp", True): channels.append("whatsapp")
    if p.get("email", True): channels.append("email")
    return tuple(channels)


def communication_plan(event, dpd_value=0, preferences=None, ptp_active=False):
    e = str(event).strip().upper()
    d = int(dpd_value or 0)
    channels = _enabled_channels(preferences)
    if e == "DUE_TODAY": return CommunicationPlan(e, "emi_due_today", channels, "payment_due")
    if e == "PAYMENT_RECEIVED": return CommunicationPlan(e, "payment_received", channels, "payment_confirmed")
    if e == "DEBIT_FAILED": return CommunicationPlan(e, "auto_debit_failed", channels, "provider_debit_failure")
    if e == "PTP_DUE": return CommunicationPlan(e, "ptp_due", channels, "promise_to_pay_due")
    if e == "DPD":
        template = "dpd_90" if d >= 90 else f"dpd_{d}"
        reason = "dpd_90_plus_escalation" if d >= 90 else "overdue_payment_reminder"
        if ptp_active: template = "dpd_ptp_follow_up"
        return CommunicationPlan(e, template, channels, reason)
    if e == "LOAN_CLOSED": return CommunicationPlan(e, "loan_closed", channels, "loan_fully_repaid")
    raise ValueError("unsupported_communication_event")


def communication_contract():
    return {
        "version": PHASE2K_VERSION,
        "channels": list(CHANNELS),
        "events": ["DUE_TODAY", "DPD", "PAYMENT_RECEIVED", "DEBIT_FAILED", "PTP_DUE", "LOAN_CLOSED"],
        "dpd_triggers": list(DEFAULT_DPD_TRIGGERS),
        "rules": {
            "provider_neutral": True,
            "transactional_only_default": True,
            "respect_customer_preferences": True,
            "no_payment_posting": True,
            "no_message_without_audit_record": True,
            "90_plus": "escalation messaging; no harassment or repeated uncontrolled sends",
        },
        "max_daily_messages": int(os.getenv("DC_MAX_DAILY_MESSAGES", "3")),
    }
