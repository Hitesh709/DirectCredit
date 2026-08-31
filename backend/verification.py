import re
from datetime import datetime
from typing import Any

PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
AADHAAR_RE = re.compile(r"^\d{12}$")


def normalize_pan(value: str) -> str:
    return re.sub(r"\s+", "", value or "").upper()


def validate_pan(value: str) -> dict[str, Any]:
    pan = normalize_pan(value)
    return {"pan": pan, "valid_format": bool(PAN_RE.fullmatch(pan)), "verification_status": "format_valid" if PAN_RE.fullmatch(pan) else "invalid_format", "source": "DirectCredit"}


def mask_aadhaar(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    return "XXXX-XXXX-" + digits[-4:] if len(digits) == 12 else ""


def validate_aadhaar(value: str) -> dict[str, Any]:
    digits = re.sub(r"\D", "", value or "")
    valid = bool(AADHAAR_RE.fullmatch(digits))
    return {"aadhaar_masked": mask_aadhaar(digits), "valid_format": valid, "verification_status": "ocr_ready" if valid else "invalid_format", "source": "DirectCredit", "government_verification": "pending_authorized_provider"}


def compare_identity(extracted: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    checks = {}
    if extracted.get("name") and profile.get("name"):
        checks["name"] = extracted["name"].strip().casefold() == profile["name"].strip().casefold()
    if extracted.get("date_of_birth") and profile.get("date_of_birth"):
        checks["date_of_birth"] = extracted["date_of_birth"] == profile["date_of_birth"]
    return {"checks": checks, "match": all(checks.values()) if checks else False, "checked_at": datetime.utcnow().isoformat()}
