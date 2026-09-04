from backend.task_31_50_contracts import validate_mbl_request


def test_mbl_request_contract():
    assert validate_mbl_request(5000, 3) == []
    assert validate_mbl_request(15000, 12) == []
    assert "requested_amount_outside_mbl_range" in validate_mbl_request(16000, 6)
    assert "unsupported_tenure" in validate_mbl_request(10000, 5)
