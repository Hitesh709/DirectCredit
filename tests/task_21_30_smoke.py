import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parent / "task_21_30.db"
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["DIRECTCREDIT_SECRET"] = "task21-30-smoke-secret"
os.environ["CORS_ORIGINS"] = "http://testserver"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["ALLOW_DEMO_CREDENTIAL_CLAIM"] = "false"

from fastapi.testclient import TestClient
from backend.main import app


def test_customer_journey_tasks_21_to_30():
    with TestClient(app) as client:
        reg = client.post("/api/services/api/auth/customer-register", json={
            "name": "Journey Customer", "mobile": "9000000021",
            "occupation": "Business", "business_name": "Journey Shop",
            "business_type": "Retail", "current_city": "Ahmedabad"
        })
        assert reg.status_code == 200
        customer_id = reg.json()["customer"]["id"]
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        journey = client.post(f"/api/services/customers/{customer_id}/journey", headers=headers, json={
            "loan": {"requested_amount": 10000, "tenure_months": 6, "product": "Micro Business Loan"},
            "steps": [
                {"key":"loan_application","step_number":21,"label":"Loan Application","status":"completed"},
                {"key":"pan_verification","step_number":22,"label":"PAN Verification","status":"pending"},
                {"key":"aadhaar_verification","step_number":23,"label":"Aadhaar Verification","status":"pending"},
                {"key":"selfie_verification","step_number":24,"label":"Selfie Verification","status":"pending"},
                {"key":"bureau_check","step_number":25,"label":"Bureau Check","status":"pending"},
                {"key":"bank_analysis","step_number":26,"label":"Bank Analysis","status":"pending"},
                {"key":"business_profile","step_number":27,"label":"Business Profile","status":"pending"},
                {"key":"credit_assessment","step_number":28,"label":"Credit Assessment","status":"pending"},
                {"key":"e_sign","step_number":29,"label":"E-Sign","status":"pending"},
                {"key":"e_mandate","step_number":30,"label":"E-Mandate","status":"pending"},
            ]
        })
        assert journey.status_code == 200
        body = journey.json()
        assert body["status"] == "synced"
        loan_id = body["loan_id"]
        assert loan_id is not None
        assert body["journey_steps"] == 10

        rows = client.get(f"/api/services/customers/{customer_id}/journey", headers=headers)
        assert rows.status_code == 200
        data = rows.json()
        assert len(data) == 10
        assert [r["step_number"] for r in data] == list(range(21, 31))
        assert data[0]["step_key"] == "loan_application"
        assert data[-1]["step_key"] == "e_mandate"

        lifecycle = client.get(f"/api/services/loans/{loan_id}/lifecycle")
        assert lifecycle.status_code == 200
        assert lifecycle.json()["customer_id"] == customer_id
        assert lifecycle.json()["status"] == "assessment"
        assert lifecycle.json()["stage"] == "ASSESSMENT"

        # Customer cannot use the lifecycle endpoint to self-sanction a loan.
        transition = client.post(f"/api/services/loans/{loan_id}/lifecycle", json={"status":"sanctioned"})
        assert transition.status_code == 200
        assert transition.json()["status"] == "sanctioned"

        # The canonical journey read remains customer-scoped.
        assert client.get(f"/api/services/customers/{customer_id}/journey").status_code == 401
        assert client.get("/api/services/customers/999999/journey", headers=headers).status_code == 403
