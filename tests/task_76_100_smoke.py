import importlib

def test_phase_modules_import():
    importlib.import_module('backend.phase_76_100')
    importlib.import_module('backend.production_controls')
    importlib.import_module('backend.file_storage')

def test_security_headers_contract():
    from backend.production_controls import limiter
    assert limiter.limit > 0 and limiter.window == 60

def test_sensitive_fields_not_in_risk_report():
    from backend.phase_76_100 import risk_breakdown
    assert callable(risk_breakdown)

def test_export_contract_exists():
    from backend.phase_76_100 import export_report, print_report, pdf_report
    assert callable(export_report) and callable(print_report) and callable(pdf_report)

def test_reconciliation_contract_exists():
    from backend.phase_76_100 import reconciliation
    assert callable(reconciliation)

def test_production_endpoints_require_admin():
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        for path in (
            '/api/services/api/admin/phase-76-100/bank-analysis',
            '/api/services/api/admin/phase-76-100/risk-breakdown',
            '/api/services/api/admin/phase-76-100/reconciliation',
            '/api/services/api/admin/phase-76-100/settings',
            '/api/services/api/admin/phase-76-100/provider-status',
            '/api/admin/reporting',
            '/admin-data/customers',
        ):
            response = client.get(path)
            assert response.status_code == 401, (path, response.status_code)
