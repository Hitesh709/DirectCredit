"""Phase 2F: e-sign and e-mandate orchestration contracts.

Provider-neutral orchestration. External providers must be configured and
confirm completion; this module never fabricates a successful signature or
mandate.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

PHASE2F_VERSION = "MBL-EXECUTION-2F-v1"
ESIGN_PROVIDER = "DC_ESIGN_URL"
MANDATE_PROVIDER = "DC_MANDATE_URL"
MANDATE_TYPES = ("NACH", "UPI_AUTOPAY")
MANDATE_FREQUENCIES = ("MONTHLY",)


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def provider_config(kind: str) -> dict[str, Any]:
    prefix = ESIGN_PROVIDER if kind == "esign" else MANDATE_PROVIDER
    return {"kind": kind, "url": os.getenv(prefix, "").strip(),
            "token_configured": bool(os.getenv(prefix.replace("_URL", "_TOKEN"), "").strip())}


def execution_contract() -> dict[str, Any]:
    return {
        "version": PHASE2F_VERSION,
        "esign": {"states": ["NOT_STARTED", "PENDING", "SIGNED", "FAILED", "EXPIRED"], "provider_config_key": ESIGN_PROVIDER},
        "mandate": {"types": list(MANDATE_TYPES), "frequencies": list(MANDATE_FREQUENCIES),
                     "states": ["NOT_STARTED", "PENDING", "ACTIVE", "FAILED", "CANCELLED"],
                     "provider_config_key": MANDATE_PROVIDER},
        "required_sequence": ["CUSTOMER_APPROVED", "ESIGN_SIGNED", "MANDATE_ACTIVE", "DISBURSEMENT_PENDING"],
        "principles": ["provider-confirmed status only", "idempotent requests", "auditable callbacks", "no disbursement before active mandate"],
    }


def mandate_amount(*, emi: float, requested_amount: float) -> float:
    # Mandate maximum is the greater of EMI and requested loan amount so a
    # provider can support its own retry/penalty rules without exceeding the
    # documented loan ceiling.
    return round(max(float(emi or 0), float(requested_amount or 0)), 2)


def make_request_id() -> str:
    return str(uuid.uuid4())


def callback_signature(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def verify_callback(payload: str, supplied_signature: str, secret: str) -> bool:
    if not secret or not supplied_signature:
        return False
    expected = callback_signature(payload, secret)
    return hmac.compare_digest(expected, supplied_signature)


def build_esign_request(*, customer_id: int, loan_id: int, offer_id: str, agreement_version: str) -> dict[str, Any]:
    config = provider_config("esign")
    if not config["url"] or not config["token_configured"]:
        return {"status": "NOT_CONFIGURED", "provider": "unconfigured", "request_id": None,
                "reason": "esign_provider_not_configured"}
    return {"status": "PENDING", "provider": "configured", "request_id": make_request_id(),
            "customer_id": customer_id, "loan_id": loan_id, "offer_id": offer_id,
            "agreement_version": agreement_version, "created_at": _utc().isoformat()}


def build_mandate_request(*, customer_id: int, loan_id: int, offer_id: str, emi: float,
                          requested_amount: float, mandate_type: str = "UPI_AUTOPAY") -> dict[str, Any]:
    mandate_type = str(mandate_type).upper()
    if mandate_type not in MANDATE_TYPES:
        raise ValueError("unsupported_mandate_type")
    config = provider_config("mandate")
    if not config["url"] or not config["token_configured"]:
        return {"status": "NOT_CONFIGURED", "provider": "unconfigured", "request_id": None,
                "reason": "mandate_provider_not_configured"}
    return {"status": "PENDING", "provider": "configured", "request_id": make_request_id(),
            "customer_id": customer_id, "loan_id": loan_id, "offer_id": offer_id,
            "mandate_type": mandate_type, "frequency": "MONTHLY",
            "maximum_amount": mandate_amount(emi=emi, requested_amount=requested_amount),
            "created_at": _utc().isoformat()}
