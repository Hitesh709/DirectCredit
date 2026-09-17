"""Phase 2R - Regulatory & Compliance Control Engine.

Provider-neutral control layer. It evaluates evidence already held by DirectCredit and
never claims regulatory compliance merely because a control is present. Unknown or
missing evidence produces REVIEW rather than an automatic pass.
"""
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

PHASE2R_VERSION = "MBL-COMPLIANCE-2R-v1"

STATUSES = ("PASS", "REVIEW", "FAIL")

REQUIRED_CONSENTS = {
    "KYC": "kyc",
    "CREDIT_BUREAU": "credit_bureau",
    "ACCOUNT_AGGREGATOR": "account_aggregator",
}

@dataclass(frozen=True)
class ComplianceCheck:
    code: str
    status: str
    reason: str
    evidence: Dict[str, Any]


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_verified(value: Any) -> bool:
    return _norm(value) in {"verified", "valid", "active", "passed", "pass", "approved"}


def _check(code: str, status: str, reason: str, evidence: Dict[str, Any] | None = None) -> ComplianceCheck:
    return ComplianceCheck(code, status, reason, evidence or {})


def evaluate_compliance(*, kyc_status: Any = None, pan_status: Any = None,
                        identity_status: Any = None, address_status: Any = None,
                        business_status: Any = None, primary_bank_status: Any = None,
                        consents: Iterable[Dict[str, Any]] = (),
                        aml_screening_status: Any = None,
                        sanctions_screening_status: Any = None,
                        audit_event_count: int | None = None) -> Dict[str, Any]:
    """Evaluate evidence without inventing provider results.

    FAIL is reserved for an explicitly negative/revoked result. Missing or unknown
    evidence is REVIEW so a missing integration cannot silently become a pass.
    """
    checks: List[ComplianceCheck] = []

    kyc_values = {"kyc": kyc_status, "pan": pan_status, "identity": identity_status,
                  "address": address_status, "business": business_status}
    for code, value in kyc_values.items():
        if _norm(value) in {"failed", "rejected", "blocked", "revoked", "invalid"}:
            checks.append(_check(f"KYC_{code.upper()}", "FAIL", "explicit_negative_status", {"status": value}))
        elif _is_verified(value):
            checks.append(_check(f"KYC_{code.upper()}", "PASS", "verified", {"status": value}))
        else:
            checks.append(_check(f"KYC_{code.upper()}", "REVIEW", "missing_or_unknown_evidence", {"status": value}))

    if _norm(primary_bank_status) in {"failed", "rejected", "blocked", "invalid"}:
        checks.append(_check("BANK_OWNERSHIP", "FAIL", "explicit_negative_status", {"status": primary_bank_status}))
    elif _is_verified(primary_bank_status):
        checks.append(_check("BANK_OWNERSHIP", "PASS", "verified", {"status": primary_bank_status}))
    else:
        checks.append(_check("BANK_OWNERSHIP", "REVIEW", "missing_or_unknown_evidence", {"status": primary_bank_status}))

    consent_map: Dict[str, List[Dict[str, Any]]] = {}
    for consent in consents or ():
        consent_map.setdefault(_norm(consent.get("consent_type")), []).append(consent)
    for label, key in REQUIRED_CONSENTS.items():
        rows = consent_map.get(key, [])
        active = any(bool(r.get("accepted")) and not r.get("withdrawn_at") for r in rows)
        if active:
            checks.append(_check(f"CONSENT_{label}", "PASS", "active_consent", {"count": len(rows)}))
        else:
            checks.append(_check(f"CONSENT_{label}", "REVIEW", "missing_or_withdrawn_consent", {"count": len(rows)}))

    for code, value in (("AML_SCREENING", aml_screening_status), ("SANCTIONS_SCREENING", sanctions_screening_status)):
        if _norm(value) in {"failed", "hit", "blocked", "rejected", "match"}:
            checks.append(_check(code, "FAIL", "explicit_screening_hit_or_failure", {"status": value}))
        elif _is_verified(value):
            checks.append(_check(code, "PASS", "screening_cleared", {"status": value}))
        else:
            checks.append(_check(code, "REVIEW", "provider_evidence_not_available", {"status": value}))

    if audit_event_count is None:
        checks.append(_check("AUDIT_TRAIL", "REVIEW", "audit_evidence_not_supplied", {}))
    elif audit_event_count > 0:
        checks.append(_check("AUDIT_TRAIL", "PASS", "audit_events_present", {"count": audit_event_count}))
    else:
        checks.append(_check("AUDIT_TRAIL", "REVIEW", "no_audit_events_found", {"count": audit_event_count}))

    failed = [c.code for c in checks if c.status == "FAIL"]
    review = [c.code for c in checks if c.status == "REVIEW"]
    passed = [c.code for c in checks if c.status == "PASS"]
    overall = "FAIL" if failed else ("REVIEW" if review else "PASS")
    return {
        "version": PHASE2R_VERSION,
        "status": overall,
        "checks": [c.__dict__ for c in checks],
        "passed_checks": passed,
        "review_checks": review,
        "failed_checks": failed,
        "control_count": len(checks),
        "principle": "Unknown evidence never becomes an automatic compliance pass.",
    }


def compliance_contract() -> Dict[str, Any]:
    return {
        "version": PHASE2R_VERSION,
        "purpose": "Regulatory and compliance control evidence orchestration",
        "statuses": list(STATUSES),
        "required_consents": list(REQUIRED_CONSENTS.values()),
        "controls": [
            "KYC evidence", "PAN/identity/address/business verification", "bank ownership",
            "consent evidence", "AML screening", "sanctions screening", "audit trail"
        ],
        "rules": [
            "No fabricated provider result",
            "Missing/unknown evidence requires review",
            "Explicit negative screening or verification results fail the control",
            "This engine is a control/evidence layer and does not by itself certify legal or regulatory compliance",
        ],
    }
