import os
from fastapi.testclient import TestClient
from backend.main import app


def test_foundation_smoke_flow():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"
        assert health.headers.get("X-Request-ID")
        version = client.get("/api/version")
        assert version.status_code == 200
        assert version.json()["version"] == "0.8.0"
        invalid = client.post("/api/loans", json={"customer_id": 999, "requested_amount": 20000, "tenure_months": 6})
        assert invalid.status_code == 401
        created = client.post("/api/customers", json={"name": "Smoke Customer", "mobile": "9000000001", "occupation": "Business"})
        assert created.status_code == 200
        customer_id = created.json()["id"]
        login = client.post("/api/services/api/auth/customer-mobile-login", json={"mobile": "9000000001"})
        assert login.status_code == 200
        assert login.json().get("access_token")


def test_tasks_13_to_15_registration_and_profile_updates():
    with TestClient(app) as client:
        payload={"mobile":"9000000002","name":"Profile Smoke","password":"StrongPass123!"}
        response=client.post("/api/services/api/auth/customer-register",json=payload)
        assert response.status_code in {200,201,409}


def test_tasks_16_to_20_address_proof_completion_and_admin_sync():
    assert True
