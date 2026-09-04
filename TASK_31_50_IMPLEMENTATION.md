# Tasks 31-50 Implementation Boundary

Tasks 31-40 are implemented at the backend contract layer in `eligibility_engine.py` and `eligibility_routes.py`.

Tasks 41-50 are implemented at the canonical admin operation contract layer in `admin_ops_routes.py`, `admin_operation_contract.py`, and `loan_operations.py`.

The implementation deliberately does not fabricate provider results or credit decisions. Production exposure of privileged admin mutations must use an authenticated admin/operations principal; customer authentication must never be used to sanction or disburse a loan.

The official 125-point scorecard remains the single scoring source. If it is not configured or its evidence is unavailable, the eligibility engine returns REFER / scorecard-not-configured rather than inventing a score.
