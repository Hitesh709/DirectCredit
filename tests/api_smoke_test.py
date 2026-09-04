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
        assert invalid.json()["meta"]["request_id"]

        created = client.post("/api/customers", json={"name": "Smoke Customer", "mobile": "9000000001", "occupation": "Business"})
        assert created.status_code == 200
        customer_id = created.json()["id"]
        assert created.json()["customer_code"].startswith("CUST")

        login = client.post("/api/services/api/auth/customer-mobile-login", json={"mobile": "9000000001"})
        assert login.status_code == 200
        body = login.json()
        assert body["customer"]["id"] == customer_id
        token = body["access_token"]
        refresh_token = body["refresh_token"]
        assert "password_hash" not in body["customer"]

        missing_login = client.post("/api/services/api/auth/customer-mobile-login", json={"mobile": "9000000099"})
        assert missing_login.status_code == 404

        headers = {"Authorization": f"Bearer {token}"}
        me = client.get("/api/customer/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["id"] == customer_id

        session = client.get("/api/services/api/auth/customer-session", headers=headers)
        assert session.status_code == 200
        assert session.json()["authenticated"] is True
        assert session.json()["customer_id"] == customer_id

        refreshed = client.post("/api/services/api/auth/refresh", json={"refresh_token": refresh_token})
        assert refreshed.status_code == 200
        assert refreshed.json()["access_token"]

        loan = client.post("/api/loans", json={"customer_id": customer_id, "requested_amount": 10000, "tenure_months": 6})
        assert loan.status_code == 200
        loan_id = loan.json()["id"]
        assert loan.json()["requested_amount"] == 10000

        schedule = client.post(f"/api/loans/{loan_id}/repayment-schedule")
        assert schedule.status_code == 200
        assert len(schedule.json()) == 6

        repayment_ledger = client.get(f"/api/services/repayments/loan/{loan_id}", headers=headers)
        assert repayment_ledger.status_code == 200
        assert len(repayment_ledger.json()) == 6
        assert {"due_amount", "paid_amount", "unpaid_amount", "status", "dpd"}.issubset(repayment_ledger.json()[0])

        document = client.post("/api/documents", json={
            "customer_id": customer_id,
            "loan_id": loan_id,
            "document_type": "PAN",
            "document_role": "identity",
            "file_name": "pan.pdf",
            "mime_type": "application/pdf",
            "file_size": 1024,
        })
        assert document.status_code == 200
        assert document.json()["verification_status"] == "pending"

        audits = client.get("/api/audit/events", params={"customer_id": customer_id, "limit": 50})
        assert audits.status_code == 200
        actions = {item["action"] for item in audits.json()}
        assert "CUSTOMER_CREATED" in actions
        assert "LOAN_APPLICATION_CREATED" in actions
        assert "DOCUMENT_RECEIVED" in actions

        logout = client.post("/api/services/api/auth/logout", headers=headers)
        assert logout.status_code == 200
        assert logout.json()["status"] == "logged_out"
        assert client.get("/api/customer/me", headers=headers).status_code == 401
        assert client.get("/api/services/api/auth/customer-session", headers=headers).status_code == 401
        assert client.post("/api/services/api/auth/refresh", json={"refresh_token": refresh_token}).status_code == 401


def test_migration_head_contains_repayment_and_session_contracts():
    inspector = inspect(engine)
    assert "customers" in inspector.get_table_names()
    assert "loan_applications" in inspector.get_table_names()
    assert "documents" in inspector.get_table_names()
    assert "repayments" in inspector.get_table_names()
    assert "customer_journey" in inspector.get_table_names()
    assert "audit_events" in inspector.get_table_names()
    customer_columns = {c["name"] for c in inspector.get_columns("customers")}
    assert "session_version" in customer_columns
    repayment_columns = {c["name"] for c in inspector.get_columns("repayments")}
    assert {"payment_reference", "payment_method", "paid_at", "bounce_reason"}.issubset(repayment_columns)
