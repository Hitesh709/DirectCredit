"""Phase 2C: configurable external-data provider gateway.

Providers are disabled until explicitly configured with environment variables.
This module never fabricates provider data. Each response is normalized and
returned with provenance, status and a request id so the credit engine can
remain evidence-driven and auditable.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROVIDER_KINDS = ("account_aggregator", "bureau", "gst", "itr", "trade", "geo")


def _env(kind: str, suffix: str, default: str = "") -> str:
    return os.getenv(f"DC_{kind.upper()}_{suffix}", default).strip()


def provider_config(kind: str) -> dict[str, Any]:
    key = kind.lower()
    if key not in PROVIDER_KINDS:
        raise ValueError("unsupported_provider")
    endpoint = _env(key, "URL")
    token = _env(key, "TOKEN")
    secret = _env(key, "SIGNING_SECRET")
    timeout = int(_env(key, "TIMEOUT_SECONDS", "15") or 15)
    return {"kind": key, "configured": bool(endpoint and token), "endpoint": endpoint,
            "has_token": bool(token), "has_signing_secret": bool(secret), "timeout_seconds": timeout}


def provider_status() -> dict[str, Any]:
    return {kind: provider_config(kind) | {"endpoint": "configured" if provider_config(kind)["endpoint"] else None}
            for kind in PROVIDER_KINDS}


def _signature(secret: str, body: bytes, timestamp: str) -> str:
    message = timestamp.encode() + b"." + body
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def _normalize(kind: str, payload: Any) -> dict[str, Any]:
    """Normalize common provider fields without assuming provider-specific schemas."""
    data = payload if isinstance(payload, dict) else {"raw": payload}
    aliases = {
        "bureau": {"score": ("score", "cibil_score", "credit_score"), "report": ("report", "credit_report")},
        "gst": {"gstin": ("gstin", "gst_number"), "turnover": ("gstr3b_avg_monthly_turnover", "monthly_turnover")},
        "itr": {"income": ("itr_income", "income", "annual_income")},
        "trade": {"validations": ("trade_validations", "validation_count")},
        "geo": {"verified": ("verified", "geo_verified")},
        "account_aggregator": {"accounts": ("accounts", "bank_accounts"), "transactions": ("transactions", "bank_transactions")},
    }
    out: dict[str, Any] = {"provider_kind": kind, "raw": data}
    for target, keys in aliases.get(kind, {}).items():
        for source in keys:
            if source in data and data[source] is not None:
                out[target] = data[source]
                break
    return out


def request_provider(kind: str, payload: dict[str, Any], idempotency_key: str | None = None) -> dict[str, Any]:
    config = provider_config(kind)
    request_id = str(uuid.uuid4())
    if not config["configured"]:
        return {"status": "NOT_CONFIGURED", "provider_kind": kind, "request_id": request_id,
                "provenance": "no_external_provider", "data": {}}

    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    timestamp = str(int(time.time()))
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {_env(kind, 'TOKEN')}",
               "X-Request-ID": request_id, "Idempotency-Key": idempotency_key or request_id,
               "X-Timestamp": timestamp}
    secret = _env(kind, "SIGNING_SECRET")
    if secret:
        headers["X-Signature"] = _signature(secret, body, timestamp)
    request = Request(config["endpoint"], data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=config["timeout_seconds"]) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return {"status": "SUCCESS", "provider_kind": kind, "request_id": request_id,
                    "http_status": response.status, "provenance": "external_provider",
                    "data": _normalize(kind, parsed)}
    except HTTPError as exc:
        return {"status": "PROVIDER_ERROR", "provider_kind": kind, "request_id": request_id,
                "http_status": exc.code, "provenance": "external_provider", "error": "provider_http_error", "data": {}}
    except (URLError, TimeoutError):
        return {"status": "PROVIDER_UNAVAILABLE", "provider_kind": kind, "request_id": request_id,
                "provenance": "external_provider", "error": "provider_unavailable", "data": {}}
    except (ValueError, json.JSONDecodeError):
        return {"status": "PROVIDER_INVALID_RESPONSE", "provider_kind": kind, "request_id": request_id,
                "provenance": "external_provider", "error": "invalid_json", "data": {}}


def consent_contract(customer_id: int, purpose: str, provider: str = "account_aggregator") -> dict[str, Any]:
    return {"customer_id": customer_id, "provider": provider, "purpose": purpose,
            "consent_required": True, "status": "PENDING_CUSTOMER_CONSENT",
            "contract_version": "2C-1.0"}
