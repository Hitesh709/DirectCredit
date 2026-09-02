"""Task 7: consistent API error/response primitives and request correlation."""
from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4


def request_id() -> str:
    return str(uuid4())


def success(data: Any = None, *, message: Optional[str] = None, meta: Optional[dict] = None) -> dict:
    return {"success": True, "data": data, "error": None, "meta": meta or {}, **({"message": message} if message else {})}


def error(code: str, message: str, *, details: Any = None, request_id_value: Optional[str] = None) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message, "details": details},
        "meta": {"request_id": request_id_value} if request_id_value else {},
    }


def public_http_error(status_code: int) -> tuple[str, str]:
    mapping = {
        400: ("BAD_REQUEST", "The request could not be processed."),
        401: ("UNAUTHORIZED", "Authentication is required or the credentials are invalid."),
        403: ("FORBIDDEN", "You do not have permission to perform this operation."),
        404: ("NOT_FOUND", "The requested resource was not found."),
        409: ("CONFLICT", "The request conflicts with the current resource state."),
        422: ("VALIDATION_ERROR", "One or more request fields are invalid."),
        429: ("RATE_LIMITED", "Too many requests. Please try again later."),
    }
    return mapping.get(status_code, ("REQUEST_ERROR", "The request could not be completed."))
