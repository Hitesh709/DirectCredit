from backend.phase2r_compliance import PHASE2R_VERSION, compliance_contract, evaluate_compliance


def test_contract_version():
    assert compliance_contract()["version"] == "MBL-COMPLIANCE-2R-v1"


def test_clean_controls_pass():
    r = evaluate_compliance(
        kyc_status="verified", pan_status="verified", identity_status="verified",
        address_status="verified", business_status="verified", primary_bank_status="verified",
        consents=[
            {"consent_type": "kyc", "accepted": True},
            {"consent_type": "credit_bureau", "accepted": True},
            {"consent_type": "account_aggregator", "accepted": True},
        ],
        aml_screening_status="clear", sanctions_screening_status="clear", audit_event_count=3,
    )
    assert r["version"] == PHASE2R_VERSION
    assert r["status"] == "PASS"
    assert r["failed_checks"] == []
    assert r["review_checks"] == []


def test_unknown_evidence_requires_review():
    r = evaluate_compliance()
    assert r["status"] == "REVIEW"
    assert r["review_checks"]
    assert r["failed_checks"] == []


def test_explicit_negative_status_fails():
    r = evaluate_compliance(kyc_status="verified", pan_status="rejected")
    assert r["status"] == "FAIL"
    assert "KYC_PAN" in r["failed_checks"]


def test_withdrawn_consent_requires_review():
    r = evaluate_compliance(
        kyc_status="verified", pan_status="verified", identity_status="verified",
        address_status="verified", business_status="verified", primary_bank_status="verified",
        consents=[{"consent_type": "kyc", "accepted": True, "withdrawn_at": "2026-09-17T10:00:00"}],
        aml_screening_status="clear", sanctions_screening_status="clear", audit_event_count=1,
    )
    assert r["status"] == "REVIEW"
    assert "CONSENT_KYC" in r["review_checks"]
