import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parent / "smoke_test.db"
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["DIRECTCREDIT_SECRET"] = "task10-smoke-secret"
os.environ["CORS_ORIGINS"] = "http://testserver"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["ALLOW_DEMO_CREDENTIAL_CLAIM"] = "false"

from fastapi.testclient import TestClient
from sqlalchemy import inspect
from backend.database import engine
from backend.main import app


def test_foundation_smoke_flow():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"
        assert health.headers.get("X-Request-ID")
        version = client.get("/api/version")
        assert version.status_code == 200
        assert version.json()["version"] == "0.7.2"
        invalid = client.post("/api/loans", json={"customer_id": 999, "requested_amount": 20000, "tenure_months": 6})
        assert invalid.status_code == 422
        assert invalid.json()["success"] is False
        assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
        created = client.post("/api/customers", json={"name": "Smoke Customer", "mobile": "9000000001", "occupation": "Business"})
        assert created.status_code == 200
        customer_id = created.json()["id"]
        login = client.post("/api/services/api/auth/customer-mobile-login", json={"mobile": "9000000001"})
        assert login.status_code == 200
        body = login.json(); token = body["access_token"]; refresh_token = body["refresh_token"]
        assert body["customer"]["id"] == customer_id
        assert "password_hash" not in body["customer"]
        assert client.post("/api/services/api/auth/customer-mobile-login", json={"mobile": "9000000099"}).status_code == 404
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/customer/me", headers=headers).json()["id"] == customer_id
        session = client.get("/api/services/api/auth/customer-session", headers=headers)
        assert session.status_code == 200 and session.json()["authenticated"] is True
        assert client.post("/api/services/api/auth/refresh", json={"refresh_token": refresh_token}).status_code == 200
        loan = client.post("/api/loans", json={"customer_id": customer_id, "requested_amount": 10000, "tenure_months": 6})
        assert loan.status_code == 200
        loan_id = loan.json()["id"]
        assert client.post(f"/api/loans/{loan_id}/repayment-schedule").status_code == 200
        repayment_ledger = client.get(f"/api/services/repayments/loan/{loan_id}", headers=headers)
        assert repayment_ledger.status_code == 200 and len(repayment_ledger.json()) == 6
        document = client.post("/api/documents", json={"customer_id": customer_id,"loan_id": loan_id,"document_type": "PAN","document_role": "identity","file_name": "pan.pdf","mime_type": "application/pdf","file_size": 1024})
        assert document.status_code == 200
        audits = client.get("/api/audit/events", params={"customer_id": customer_id, "limit": 50})
        assert audits.status_code == 200
        actions = {item["action"] for item in audits.json()}
        assert {"CUSTOMER_CREATED", "LOAN_APPLICATION_CREATED", "DOCUMENT_RECEIVED"}.issubset(actions)
        logout = client.post("/api/services/api/auth/logout", headers=headers)
        assert logout.status_code == 200
        assert client.get("/api/customer/me", headers=headers).status_code == 401
        assert client.get("/api/services/api/auth/customer-session", headers=headers).status_code == 401
        assert client.post("/api/services/api/auth/refresh", json={"refresh_token": refresh_token}).status_code == 401


def test_migration_head_contains_repayment_and_session_contracts():
    inspector = inspect(engine)
    assert {"customers", "loan_applications", "documents", "repayments", "customer_journey", "audit_events"}.issubset(inspector.get_table_names())
    assert "session_version" in {c["name"] for c in inspector.get_columns("customers")}
    assert {"payment_reference", "payment_method", "paid_at", "bounce_reason"}.issubset({c["name"] for c in inspector.get_columns("repayments")})


def test_tasks_13_to_15_registration_and_profile_updates():
    with TestClient(app) as client:
        registration = client.post("/api/services/api/auth/customer-register", json={"name":"Task Customer","mobile":"9000000013","occupation":"Business","business_name":"Task Business","business_type":"Retail"})
        assert registration.status_code == 200
        body = registration.json(); customer = body["customer"]; customer_id = customer["id"]
        assert body["registered"] is True and body["auth_method"] == "mobile_direct"
        assert customer["customer_code"].startswith("CUST")
        assert client.post("/api/services/api/auth/customer-register", json={"name":"Duplicate","mobile":"9000000013"}).status_code == 409
        login = client.post("/api/services/api/auth/customer-mobile-login", json={"mobile":"9000000013"})
        assert login.status_code == 200 and login.json()["customer"]["id"] == customer_id
        headers={"Authorization":f"Bearer {login.json()['access_token']}"}
        personal = client.patch(f"/api/services/customer-profile/{customer_id}/personal", headers=headers, json={"name":"Updated Customer","email":"updated@example.test","current_city":"Ahmedabad"})
        assert personal.status_code == 200
        assert personal.json()["profile"]["name"] == "Updated Customer"
        employment = client.patch(f"/api/services/customer-profile/{customer_id}/employment-business", headers=headers, json={"business_name":"Updated Business","monthly_income":35000,"years_in_business":4,"existing_emi":5000})
        assert employment.status_code == 200
        assert employment.json()["profile"]["business_name"] == "Updated Business"
        assert employment.json()["profile"]["monthly_income"] == 35000
        assert client.patch(f"/api/services/customer-profile/{customer_id}/personal", json={"name":"No Auth"}).status_code == 401
