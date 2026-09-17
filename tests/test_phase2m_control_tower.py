from backend.phase2m_control_tower import PHASE2M_VERSION, aggregate, control_tower_contract

def test_contract_version():
    assert control_tower_contract()["version"] == PHASE2M_VERSION

def test_aggregate_is_zero_safe():
    result = aggregate([])
    assert result["loan_count"] == 0
    assert result["collection_rate_pct"] == 0.0
    assert result["debit_success_rate_pct"] == 0.0

def test_aggregate_totals():
    result = aggregate([
        {"due_amount":100,"paid_amount":80,"overdue_amount":20,"debit_attempts":2,"debit_successes":1,"ptp_count":1,"call_count":2,"field_visit_count":0},
        {"due_amount":200,"paid_amount":100,"overdue_amount":100,"debit_attempts":1,"debit_successes":1,"ptp_count":0,"call_count":1,"field_visit_count":1},
    ])
    assert result["loan_count"] == 2
    assert result["due_amount"] == 300
    assert result["paid_amount"] == 180
    assert result["overdue_amount"] == 120
    assert result["collection_rate_pct"] == 60.0
    assert result["debit_success_rate_pct"] == 66.67
    assert result["ptp_count"] == 1
    assert result["call_count"] == 3
    assert result["field_visit_count"] == 1
