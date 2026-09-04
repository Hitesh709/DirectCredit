"""Small pure contracts for Tasks 31-50; API layers must use canonical DB records."""
from typing import Any

MBL_MIN = 5000
MBL_MAX = 15000
MBL_TENURES = (3, 6, 9, 12)


def validate_mbl_request(amount: Any, tenure_months: Any) -> list[str]:
    errors = []
    try: amount_f = float(amount)
    except (TypeError, ValueError): amount_f = -1
    try: tenure = int(tenure_months)
    except (TypeError, ValueError): tenure = -1
    if not MBL_MIN <= amount_f <= MBL_MAX: errors.append("requested_amount_outside_mbl_range")
    if tenure not in MBL_TENURES: errors.append("unsupported_tenure")
    return errors


def decision_reasons(*reasons: str) -> list[str]:
    return [r for r in reasons if r]
