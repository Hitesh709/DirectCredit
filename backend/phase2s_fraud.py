"""Phase 2S - Fraud & Risk Intelligence Engine.

Deterministic, explainable fraud-signal layer. It does not replace policy, KYC,
credit, or human investigation and never invents external verification results.
"""
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

PHASE2S_VERSION = "MBL-FRAUD-2S-v1"
STATUSES = ("CLEAR", "REVIEW", "HIGH_RISK")

@dataclass(frozen=True)
class FraudSignal:
    code: str
    severity: str
    points: int
    reason: str
    evidence: Dict[str, Any]


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _signal(code: str, severity: str, points: int, reason: str, evidence: Dict[str, Any] | None = None) -> FraudSignal:
    return FraudSignal(code, severity, points, reason, evidence or {})


def evaluate_fraud(*, device_fingerprint: Any = None, ip_address: Any = None,
                   mobile: Any = None, pan: Any = None, bank_account_fingerprint: Any = None,
                   linked_customer_count: int = 0, application_count_24h: int = 0,
                   application_count_7d: int = 0, identity_match: Any = None,
                   bank_owner_match: Any = None, geo_distance_km: float | None = None,
                   suspicious_transactions: int = 0, duplicate_document_count: int = 0,
                   external_signals: Iterable[Dict[str, Any]] = ()) -> Dict[str, Any]:
    signals: List[FraudSignal] = []
    if linked_customer_count >= 3:
        signals.append(_signal("IDENTITY_NETWORK_LINK", "HIGH", 30, "same_identifier_linked_to_multiple_customers", {"count": linked_customer_count}))
    elif linked_customer_count == 2:
        signals.append(_signal("IDENTITY_NETWORK_LINK", "MEDIUM", 15, "identifier_shared_by_multiple_customers", {"count": linked_customer_count}))
    if application_count_24h >= 5:
        signals.append(_signal("APPLICATION_VELOCITY_24H", "HIGH", 25, "high_application_velocity", {"count": application_count_24h}))
    elif application_count_24h >= 3:
        signals.append(_signal("APPLICATION_VELOCITY_24H", "MEDIUM", 12, "elevated_application_velocity", {"count": application_count_24h}))
    if application_count_7d >= 10:
        signals.append(_signal("APPLICATION_VELOCITY_7D", "HIGH", 20, "high_weekly_application_velocity", {"count": application_count_7d}))
    elif application_count_7d >= 6:
        signals.append(_signal("APPLICATION_VELOCITY_7D", "MEDIUM", 10, "elevated_weekly_application_velocity", {"count": application_count_7d}))
    if _norm(identity_match) in {"failed", "mismatch", "no"}:
        signals.append(_signal("IDENTITY_MISMATCH", "HIGH", 35, "identity_evidence_mismatch", {"status": identity_match}))
    if _norm(bank_owner_match) in {"failed", "mismatch", "no"}:
        signals.append(_signal("BANK_OWNER_MISMATCH", "HIGH", 35, "bank_account_owner_mismatch", {"status": bank_owner_match}))
    if suspicious_transactions > 0:
        signals.append(_signal("SUSPICIOUS_TRANSACTIONS", "HIGH", min(30, 10 + suspicious_transactions * 5), "suspicious_transaction_signals_present", {"count": suspicious_transactions}))
    if duplicate_document_count > 0:
        signals.append(_signal("DUPLICATE_DOCUMENT", "HIGH", min(25, duplicate_document_count * 10), "duplicate_document_evidence", {"count": duplicate_document_count}))
    if geo_distance_km is not None and geo_distance_km > 100:
        signals.append(_signal("GEO_ANOMALY", "MEDIUM", 12, "material_distance_between_declared_and_observed_location", {"distance_km": geo_distance_km}))
    for item in external_signals or ():
        points = max(0, min(40, int(item.get("points") or 0)))
        if points:
            signals.append(_signal(str(item.get("code") or "EXTERNAL_SIGNAL"), str(item.get("severity") or "MEDIUM").upper(), points, str(item.get("reason") or "external_fraud_signal"), dict(item)))
    score = min(100, sum(s.points for s in signals))
    high = [s.code for s in signals if s.severity == "HIGH"]
    status = "HIGH_RISK" if score >= 60 or high else ("REVIEW" if score >= 20 else "CLEAR")
    return {"version": PHASE2S_VERSION, "status": status, "fraud_score": score,
            "signals": [s.__dict__ for s in signals], "high_severity_signals": high,
            "review_required": status != "CLEAR",
            "decision_rule": "Fraud intelligence is a risk signal layer; final lending action remains governed by approved policy and authorized workflow."}


def fraud_contract() -> Dict[str, Any]:
    return {"version": PHASE2S_VERSION, "purpose": "Deterministic fraud and risk signal detection",
            "statuses": list(STATUSES),
            "signals": ["device_fingerprint", "IP/mobile/PAN linkage", "bank ownership", "identity mismatch", "application velocity", "duplicate evidence", "transaction anomaly", "geo anomaly", "external signals"],
            "rules": ["Signals are explainable and evidence-backed", "No fabricated provider result", "Fraud score does not itself approve or reject a loan", "High-risk signals require controlled review or an existing approved hard-stop policy"]}
