"""Optional verification provider adapters.

DirectCredit works without external accounts. Providers are opt-in via environment
variables; no credentials are hard-coded. Until a provider is configured, the
internal validation result is returned with an explicit pending status.
"""
import os
from typing import Any

PROVIDERS = {
    "pan": os.getenv("PAN_PROVIDER", "internal"),
    "aadhaar": os.getenv("AADHAAR_PROVIDER", "internal"),
    "bureau": os.getenv("BUREAU_PROVIDER", "pending"),
    "selfie": os.getenv("SELFIE_PROVIDER", "internal"),
    "esign": os.getenv("ESIGN_PROVIDER", "pending"),
    "disbursement": os.getenv("DISBURSEMENT_PROVIDER", "pending"),
    "mandate": os.getenv("MANDATE_PROVIDER", "pending"),
}

def provider_status() -> dict[str, Any]:
    return {
        name: {"provider": provider, "configured": provider not in {"pending", "internal"}}
        for name, provider in PROVIDERS.items()
    }

def result(service: str, internal_result: dict[str, Any]) -> dict[str, Any]:
    provider = PROVIDERS.get(service, "pending")
    if provider in {"internal", "pending"}:
        return {**internal_result, "provider": provider, "external_verification": "pending" if provider == "pending" else "not_required"}
    return {**internal_result, "provider": provider, "external_verification": "adapter_ready"}
