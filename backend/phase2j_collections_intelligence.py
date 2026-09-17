"""Phase 2J collections intelligence and recovery prioritisation.

Deterministic, explainable collection prioritisation. It does not make lending
or customer eligibility decisions and never posts a payment by itself.
"""
from dataclasses import dataclass
from datetime import date, datetime
import json

from .phase2i_collections import collection_bucket, overdue_amount

PHASE2J_VERSION = "MBL-COLLECTIONS-2J-v1"

BUCKET_WEIGHT = {
    "CURRENT": 0,
    "DPD_1_7": 20,
    "DPD_8_30": 35,
    "DPD_31_60": 55,
    "DPD_61_90": 75,
    "DPD_90_PLUS": 90,
}

@dataclass(frozen=True)
class RecoveryPriority:
    score: int
    bucket: str
    urgency: str
    reason_codes: tuple[str, ...]


def priority_score(bucket, overdue_amount, max_dpd, ptp_active=False, failed_debit=False):
    score = BUCKET_WEIGHT.get(bucket, 0)
    if overdue_amount >= 50000: score += 15
    elif overdue_amount >= 25000: score += 10
    elif overdue_amount >= 10000: score += 5
    score += min(10, max(0, int(max_dpd // 15)))
    if ptp_active: score += 8
    if failed_debit: score += 7
    return min(100, score)


def urgency(score):
    if score >= 80: return "CRITICAL"
    if score >= 60: return "HIGH"
    if score >= 35: return "MEDIUM"
    return "LOW"


def build_priority(bucket, overdue_amount, max_dpd, ptp_active=False, failed_debit=False):
    codes = []
    if max_dpd > 0: codes.append("OVERDUE")
    if max_dpd >= 31: codes.append("AGING_31_PLUS_DPD")
    if max_dpd >= 90: codes.append("AGING_90_PLUS_DPD")
    if overdue_amount >= 25000: codes.append("MATERIAL_OVERDUE")
    if ptp_active: codes.append("PTP_ACTIVE")
    if failed_debit: codes.append("DEBIT_FAILED")
    score = priority_score(bucket, overdue_amount, max_dpd, ptp_active, failed_debit)
    return RecoveryPriority(score, bucket, urgency(score), tuple(codes))


def parse_action_notes(action):
    try:
        value = json.loads(action.notes or "{}")
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def latest_ptp(actions, as_of=None):
    today = as_of or date.today()
    candidates = []
    for action in actions:
        if action.action_type != "promise_to_pay": continue
        data = parse_action_notes(action)
        try: promised = datetime.strptime(str(data.get("promised_date", ""))[:10], "%Y-%m-%d").date()
        except Exception: continue
        if promised >= today and action.status == "recorded": candidates.append((promised, action))
    return max(candidates, key=lambda x: x[0])[1] if candidates else None


def has_failed_debit(actions):
    return any(x.action_type == "auto_debit_request" and x.status == "failed" for x in actions)


def recovery_action(priority, mandate_active):
    if priority.bucket == "DPD_90_PLUS": return "MANUAL_ESCALATION"
    if mandate_active and "DEBIT_FAILED" not in priority.reason_codes and priority.score >= 35:
        return "AUTO_DEBIT_REVIEW"
    if "PTP_ACTIVE" in priority.reason_codes: return "PTP_FOLLOW_UP"
    return "CUSTOMER_CONTACT"


def intelligence_contract():
    return {
        "version": PHASE2J_VERSION,
        "purpose": "explainable collection prioritisation and recovery workflow",
        "score_range": [0, 100],
        "urgency_bands": {"0-34": "LOW", "35-59": "MEDIUM", "60-79": "HIGH", "80-100": "CRITICAL"},
        "principles": [
            "deterministic and explainable",
            "no automatic payment posting",
            "provider confirmation remains mandatory",
            "customer and loan scope remains enforced at the API boundary",
            "priority is an operational queue signal, not a credit decision",
        ],
    }
