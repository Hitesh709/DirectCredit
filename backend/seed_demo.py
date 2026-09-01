from datetime import date, timedelta
from sqlalchemy.orm import Session
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord


def seed_demo_data(db: Session) -> None:
    """Create a small, reproducible demo portfolio only when the database is empty."""
    if db.query(LoanRecord).count() > 0:
        return

    names = [
        "Aarav Shah", "Priya Mehta", "Rohan Patel", "Neha Verma", "Vikram Joshi",
        "Ananya Desai", "Karan Gupta", "Meera Iyer", "Rahul Singh", "Pooja Nair",
    ]
    businesses = [
        "Shah General Store", "Mehta Foods", "Patel Electricals", "Verma Garments",
        "Joshi Hardware", "Desai Traders", "Gupta Mobile Shop", "Iyer Stationery",
        "Singh Auto Parts", "Nair Home Supplies",
    ]
    cities = ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Indore"]
    amounts = [6500, 8000, 9500, 11000, 12500, 7000, 14500, 10000, 15000, 5500]
    statuses = ["assessment", "sanctioned", "disbursed", "repayment", "active", "overdue", "overdue", "repaid", "active", "sanctioned"]
    rng_scores = [742, 768, 781, 755, 804, 721, 698, 812, 776, 731]

    for i in range(10):
        amount = float(amounts[i])
        status = statuses[i]
        customer = CustomerRecord(
            name=names[i], pan=f"DCDMO{i+1:04d}X", mobile=f"90000000{i+1:02d}",
            email=f"demo{i+1}@directcredit.test", address=f"Demo Business Address, {cities[i % len(cities)]}",
            current_city=cities[i % len(cities)], business_name=businesses[i], business_type="Proprietorship",
            date_of_birth=f"198{i % 10}-0{(i % 9) + 1}-15", aadhaar_masked=f"XXXX XXXX {1000 + i:04d}",
            customer_type="Individual", occupation="Self Employed", monthly_income=18000 + i * 2500,
            work_experience_years=4 + (i % 7), years_in_business=3 + (i % 8),
            average_bank_balance=12000 + i * 1800,
            primary_bank=["HDFC Bank", "ICICI Bank", "Axis Bank", "SBI", "Kotak Mahindra Bank"][i % 5],
            cibil_score=rng_scores[i], foir=35 + (i % 6) * 3, existing_emi=1800 + i * 250,
            dependents=1 + (i % 4), kyc_status="verified", email_verified="verified", selfie_status="verified",
        )
        db.add(customer)
        db.flush()

        disbursed = amount if status in {"disbursed", "repayment", "active", "overdue", "repaid"} else 0.0
        sanctioned = amount if status in {"sanctioned", "disbursed", "repayment", "active", "overdue", "repaid"} else 0.0
        loan = LoanRecord(
            customer_id=customer.id, requested_amount=amount, eligible_amount=amount,
            monthly_emi=round(amount / 6, 2), sanctioned_amount=sanctioned, disbursed_amount=disbursed,
            outstanding_amount=0.0, interest_rate=15.0, tenure_months=6, status=status,
            current_stage={
                "assessment": "ASSESSMENT", "sanctioned": "SANCTION", "disbursed": "DISBURSEMENT",
                "repayment": "REPAYMENT", "active": "REPAYMENT", "overdue": "REPAYMENT", "repaid": "REPAYMENT"
            }[status], product="Micro Business Loan",
        )
        db.add(loan)
        db.flush()

        paid_total = 0.0
        if disbursed > 0:
            emi = round(amount / 6, 2)
            for installment in range(1, 7):
                if status == "repaid":
                    due = emi if installment < 6 else round(amount - emi * 5, 2)
                    paid = due; repayment_status = "paid"
                    due_date = date.today() - timedelta(days=30 * (6 - installment + 1))
                elif status == "overdue" and installment == 1:
                    due = emi; paid = round(due * 0.25, 2); repayment_status = "overdue"
                    due_date = date.today() - timedelta(days=45 + i * 2)
                elif installment <= 3 and status in {"repayment", "active"}:
                    due = emi if installment < 6 else round(amount - emi * 5, 2)
                    paid = due; repayment_status = "paid"
                    due_date = date.today() - timedelta(days=30 * (4 - installment))
                else:
                    due = emi if installment < 6 else round(amount - emi * 5, 2)
                    paid = 0.0; repayment_status = "upcoming"
                    due_date = date.today() + timedelta(days=30 * (installment - 3))
                paid_total += paid
                db.add(RepaymentRecord(
                    loan_id=loan.id, installment=installment, due_date=due_date.isoformat(),
                    due_amount=due, paid_amount=paid, status=repayment_status,
                ))
        loan.outstanding_amount = round(max(amount - paid_total, 0.0), 2) if disbursed else 0.0

    db.commit()
