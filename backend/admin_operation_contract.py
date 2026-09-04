from __future__ import annotations
from typing import Any


def customer_profile_payload(customer: Any) -> dict:
    return {
        "customer_id": customer.customer_code,
        "id": customer.id,
        "name": customer.name,
        "mobile": customer.mobile,
        "email": customer.email,
        "customer_type": customer.customer_type,
        "occupation": customer.occupation,
        "business_name": customer.business_name,
        "business_type": customer.business_type,
        "city": customer.city,
        "address": customer.address,
        "permanent_address": customer.permanent_address,
        "residence_ownership": customer.residence_ownership,
        "residence_ownership_since": customer.residence_ownership_since,
    }


def document_payload(document: Any) -> dict:
    return {
        "id": document.id,
        "customer_id": document.customer_id,
        "loan_id": document.loan_id,
        "document_role": document.document_role,
        "verification_status": document.verification_status,
        "required": document.required,
    }


def loan_payload(loan: Any) -> dict:
    return {
        "loan_id": loan.id,
        "customer_id": loan.customer_id,
        "amount": loan.amount,
        "status": loan.status,
    }
