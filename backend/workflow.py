from datetime import date, timedelta
from typing import List, Dict

APPLICATION_STAGES = [
    "PAN", "AADHAAR", "SELFIE", "BUREAU", "PROFILE", "BANK_STATEMENT",
    "OTHER_DOCUMENTS", "ASSESSMENT", "SANCTION", "CUSTOMER_APPROVAL",
    "E_SIGN", "DISBURSEMENT", "REPAYMENT"
]

PRODUCT_MIN = 5000.0
PRODUCT_MAX = 15000.0


def assess_amount(requested: float) -> Dict[str, float | str]:
    if requested < PRODUCT_MIN or requested > PRODUCT_MAX:
        raise ValueError("Loan amount must be between ₹5,000 and ₹15,000")
    eligible = requested
    monthly_emi = round(eligible / 6, 2)
    return {"eligible_amount": eligible, "monthly_emi": monthly_emi, "status": "assessment"}


def build_repayment_schedule(loan_id: int, amount: float, months: int = 6) -> List[dict]:
    emi = round(amount / months, 2)
    schedule = []
    start = date.today()
    for i in range(1, months + 1):
        schedule.append({
            "loan_id": loan_id,
            "installment": i,
            "due_date": (start + timedelta(days=30 * i)).isoformat(),
            "due_amount": emi if i < months else round(amount - emi * (months - 1), 2),
            "paid_amount": 0,
            "status": "upcoming"
        })
    return schedule
