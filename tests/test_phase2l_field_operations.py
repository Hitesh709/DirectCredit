from backend.phase2l_field_operations import PHASE2L_VERSION, field_operations_contract, normalize_disposition, normalize_visit_outcome

def test_contract_version():
    assert field_operations_contract()["version"] == PHASE2L_VERSION

def test_dispositions():
    assert normalize_disposition("connected") == "CONNECTED"
    assert normalize_visit_outcome("payment_promised") == "PAYMENT_PROMISED"

def test_invalid_disposition():
    try:
        normalize_disposition("unknown")
        assert False
    except ValueError as exc:
        assert str(exc) == "unsupported_call_disposition"
