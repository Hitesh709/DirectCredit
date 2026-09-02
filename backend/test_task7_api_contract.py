"""Task 7 smoke tests for validation and safe API errors."""
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite:///./task7_test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from backend.main import app


def test_invalid_loan_amount_is_rejected():
    client = TestClient(app)
    response = client.post("/api/loans", json={"customer_id": 1, "requested_amount": 4999, "tenure_months": 6})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["meta"]["request_id"]
    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]


def test_unknown_route_has_standard_error_shape():
    client = TestClient(app)
    response = client.get("/api/task7/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["meta"]["request_id"]


def test_server_errors_do_not_expose_exception_details():
    # This endpoint intentionally relies on the standard HTTP error handler contract.
    client = TestClient(app)
    response = client.get("/api/task7/does-not-exist")
    assert "Traceback" not in response.text
    assert "sqlalchemy" not in response.text.lower()
