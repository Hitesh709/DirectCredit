import os
from backend.phase2c_provider_gateway import consent_contract, provider_config, request_provider


def test_unconfigured_provider_is_safe(monkeypatch):
    for key in ["DC_BUREAU_URL", "DC_BUREAU_TOKEN", "DC_BUREAU_SIGNING_SECRET"]:
        monkeypatch.delenv(key, raising=False)
    result = request_provider("bureau", {"pan": "REDACTED"})
    assert result["status"] == "NOT_CONFIGURED"
    assert result["provenance"] == "no_external_provider"
    assert result["data"] == {}


def test_consent_contract_requires_customer_consent():
    contract = consent_contract(42, "credit_assessment")
    assert contract["customer_id"] == 42
    assert contract["consent_required"] is True
    assert contract["status"] == "PENDING_CUSTOMER_CONSENT"


def test_provider_config_requires_url_and_token(monkeypatch):
    monkeypatch.setenv("DC_GST_URL", "https://example.invalid/gst")
    monkeypatch.delenv("DC_GST_TOKEN", raising=False)
    config = provider_config("gst")
    assert config["configured"] is False
