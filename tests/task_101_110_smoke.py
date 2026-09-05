import os
import re

def test_post_100_module_contracts():
    from backend.post_100_operations import mask_mobile, mask_pan, mask_aadhaar, validate_idempotency_key, safe_event_details, IDEMPOTENCY_RE
    assert mask_mobile("9876543210") == "******3210"
    assert mask_pan("ABCDE1234F") == "AB******4F"
    assert mask_aadhaar("123456789012") == "XXXX-XXXX-9012"
    assert validate_idempotency_key("loan:123:attempt1")
    assert IDEMPOTENCY_RE.fullmatch("customer_123_attempt1")
    assert not IDEMPOTENCY_RE.fullmatch("bad key")
    safe=safe_event_details({"pan":"ABCDE1234F","mobile":"9876543210","ok":1})
    assert safe["pan"] == "[REDACTED]" and safe["mobile"] != "9876543210" if "mobile" in safe else safe["pan"] == "[REDACTED]"

def test_post_100_router_is_integrated():
    from backend.api_services import router
    paths={getattr(r,"path","") for r in router.routes}
    assert "/api/admin/post-100/data-contract" in paths
    assert "/api/admin/post-100/release-readiness" in paths
    assert "/api/admin/post-100/providers" in paths

def test_post_100_security_contract_is_admin_scoped():
    from backend.post_100_operations import router
    for route in router.routes:
        if getattr(route,"path",""):
            deps=getattr(route,"dependant",None)
            assert deps is not None
            assert any(getattr(d.call,"__name__","")=="get_current_admin" for d in deps.dependencies)

def test_no_live_secret_is_defined_in_post_100_module():
    source=open(os.path.join(os.path.dirname(__file__),"..","backend","post_100_operations.py"),encoding="utf-8").read()
    assert "DIRECTCREDIT_SECRET=\"" not in source
    assert not re.search(r"api[_-]?key\s*=\s*['\"]\w+['\"]", source, re.I)
