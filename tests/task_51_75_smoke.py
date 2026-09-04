import importlib

def test_servicing_modules_import():
    importlib.import_module("backend.servicing_models")
    importlib.import_module("backend.servicing_routes")
    importlib.import_module("backend.analytics_routes")
    importlib.import_module("backend.report_routes_v2")

def test_dpd_and_foreclosure_contract():
    from backend.repayment_contract import calculate_dpd
    assert calculate_dpd("2099-01-01",0,100)==0

def test_admin_guard_requires_credentials():
    from backend.admin_auth import get_current_admin
    from fastapi import HTTPException
    try:
        get_current_admin(None)
        assert False
    except HTTPException as exc:
        assert exc.status_code==401
