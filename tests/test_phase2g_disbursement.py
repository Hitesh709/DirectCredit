import os
from datetime import date

from backend.phase2g_disbursement import (
    PHASE2G_VERSION,
    build_disbursement_request,
    callback_signature,
    disbursement_contract,
    repayment_schedule,
    verify_callback,
)


def test_contract_requires_active_mandate_and_verified_beneficiary():
    contract = disbursement_contract()
    assert contract["version"] == PHASE2G_VERSION
    assert "MANDATE_ACTIVE" in contract["required_preconditions"]
    assert "VALID_BENEFICIARY_BANK_ACCOUNT" in contract["required_preconditions"]


def test_unconfigured_provider_is_safe(monkeypatch):
    monkeypatch.delenv("DC_DISBURSEMENT_URL", raising=False)
    monkeypatch.delenv("DC_DISBURSEMENT_TOKEN", raising=False)
    result = build_disbursement_request(customer_id=1, loan_id=2, amount=10000, beneficiary={"ifsc": "TEST0001"})
    assert result["status"] == "NOT_STARTED"
    assert result["request_id"] is None


def test_callback_signature_round_trip():
    body = '{"loan_id":2,"status":"SUCCESS"}'
    signature = callback_signature(body, "secret")
    assert verify_callback(body, signature, "secret")
    assert not verify_callback(body, signature + "x", "secret")


def test_repayment_schedule_principal_and_tenure():
    rows = repayment_schedule(loan_id=7, principal=12000, annual_rate=18, tenure_months=6, first_due_date=date(2026, 10, 1))
    assert len(rows) == 6
    assert rows[0]["installment"] == 1
    assert rows[-1]["due_date"] == "2027-02-28"
    assert round(sum(r["principal_component"] for r in rows), 2) == 12000
    assert all(r["due_amount"] > 0 for r in rows)
