import json
import os
from backend.phase2f_execution import build_esign_request, build_mandate_request, execution_contract, callback_signature, verify_callback


def test_contract_has_required_sequence():
    c=execution_contract()
    assert c["version"] == "MBL-EXECUTION-2F-v1"
    assert c["required_sequence"] == ["CUSTOMER_APPROVED","ESIGN_SIGNED","MANDATE_ACTIVE","DISBURSEMENT_PENDING"]


def test_unconfigured_providers_are_safe():
    os.environ.pop("DC_ESIGN_URL",None); os.environ.pop("DC_ESIGN_TOKEN",None)
    os.environ.pop("DC_MANDATE_URL",None); os.environ.pop("DC_MANDATE_TOKEN",None)
    e=build_esign_request(customer_id=1,loan_id=2,offer_id="o",agreement_version="v1")
    m=build_mandate_request(customer_id=1,loan_id=2,offer_id="o",emi=5000,requested_amount=100000)
    assert e["status"] == "NOT_CONFIGURED"
    assert m["status"] == "NOT_CONFIGURED"


def test_callback_signature():
    body=json.dumps({"loan_id":2,"status":"SIGNED"},sort_keys=True)
    sig=callback_signature(body,"secret")
    assert verify_callback(body,sig,"secret")
    assert not verify_callback(body,sig,"wrong")


def test_mandate_uses_loan_ceiling():
    os.environ["DC_MANDATE_URL"]="https://provider.invalid/mandate"
    os.environ["DC_MANDATE_TOKEN"]="test"
    m=build_mandate_request(customer_id=1,loan_id=2,offer_id="o",emi=5000,requested_amount=100000)
    assert m["maximum_amount"] == 100000
