import json
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, DocumentRecord, CustomerJourneyRecord, BankTransactionRecord


def profile_payload(customer_id: int, db: Session) -> dict:
    c = db.get(CustomerRecord, customer_id)
    if not c:
        return None
    loans = db.query(LoanRecord).filter(LoanRecord.customer_id == customer_id).order_by(LoanRecord.id.desc()).all()
    ids = [x.id for x in loans]
    repayments = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id.in_(ids)).order_by(RepaymentRecord.id.desc()).all() if ids else []
    docs = db.query(DocumentRecord).filter(DocumentRecord.customer_id == customer_id).order_by(DocumentRecord.id.desc()).all()
    journey = db.query(CustomerJourneyRecord).filter(CustomerJourneyRecord.customer_id == customer_id).order_by(CustomerJourneyRecord.step_number).all()
    transactions = db.query(BankTransactionRecord).filter(BankTransactionRecord.customer_id == customer_id).order_by(BankTransactionRecord.transaction_date.desc(), BankTransactionRecord.id.desc()).all()
    sanctioned = sum(x.sanctioned_amount or 0 for x in loans)
    outstanding = sum(x.outstanding_amount or 0 for x in loans)
    paid = sum(x.paid_amount or 0 for x in repayments)
    overdue = sum(max((x.due_amount or 0) - (x.paid_amount or 0), 0) for x in repayments if x.status == "overdue")

    monthly = defaultdict(lambda: {"credits": 0.0, "debits": 0.0, "transactions": 0, "closing_balance": None, "average_balance": None})
    balances = defaultdict(list)
    categories = Counter()
    negative_balance = 0
    for t in transactions:
        month = str(t.transaction_date or "")[:7] or "unknown"
        row = monthly[month]; row["transactions"] += 1
        amount = float(t.amount or 0)
        if str(t.direction).lower() == "credit": row["credits"] += amount
        else: row["debits"] += amount
        if t.balance is not None:
            row["closing_balance"] = t.balance
            balances[month].append(float(t.balance))
            if float(t.balance) < 0: negative_balance += 1
        if t.category: categories[t.category] += 1
    for month, row in monthly.items():
        vals = balances.get(month, [])
        row["average_balance"] = round(sum(vals) / len(vals), 2) if vals else None
        row["credits"] = round(row["credits"], 2); row["debits"] = round(row["debits"], 2)
    total_credits = round(sum(x["credits"] for x in monthly.values()), 2)
    total_debits = round(sum(x["debits"] for x in monthly.values()), 2)
    months = max(1, len([m for m in monthly if m != "unknown"]))
    bank = {
        "total_transactions": len(transactions), "credit_transactions": sum(str(t.direction).lower() == "credit" for t in transactions),
        "debit_transactions": sum(str(t.direction).lower() == "debit" for t in transactions),
        "last_balance": next((t.balance for t in transactions if t.balance is not None), None),
        "average_eod_balance": round(sum(float(t.balance) for t in transactions if t.balance is not None) / max(1, sum(t.balance is not None for t in transactions)), 2) if any(t.balance is not None for t in transactions) else c.average_bank_balance,
        "average_monthly_credit": round(total_credits / months, 2) if transactions else None,
        "average_monthly_debit": round(total_debits / months, 2) if transactions else None,
        "negative_balance_count": negative_balance,
        "top_categories": [{"category": k, "count": v} for k, v in categories.most_common(10)],
        "monthly_breakdown": [{"month": k, **v} for k, v in sorted(monthly.items())],
        "status": "Connected transaction data" if transactions else "No bank transaction data connected",
    }

    latest_scored = next((x for x in loans if x.scorecard_score is not None), None)
    if latest_scored:
        reasons = json.loads(latest_scored.scorecard_reasons or "[]")
        hard = json.loads(latest_scored.scorecard_hard_rejects or "[]")
        factors = json.loads(latest_scored.scorecard_factor_scores or "{}")
        score = latest_scored.scorecard_score
        decision = latest_scored.scorecard_decision or "NOT_ASSESSED"
        tier = "High Risk" if decision == "REJECT" else "Low Risk" if score >= 105 else "Moderate Risk" if score >= 95 else "Manual Review"
        risk = {"total_score": score, "max_score": latest_scored.scorecard_max or 125, "source": "scorecard", "scorecard_version": latest_scored.scorecard_version, "risk_tier": tier, "decision": decision, "approval_percent": latest_scored.scorecard_approval_percent, "reasons": reasons, "hard_rejects": hard, "factor_scores": factors, "credit_score": c.cibil_score, "monthly_income": c.monthly_income, "foir": c.foir, "existing_emi": c.existing_emi}
    else:
        risk = {"total_score": None,"max_score":125,"source":"scorecard_not_configured","risk_tier":"Not assessed","decision":"Not assessed","approval_percent":None,"reasons":[],"hard_rejects":[],"factor_scores":{},"credit_score":c.cibil_score,"monthly_income":c.monthly_income,"foir":c.foir,"existing_emi":c.existing_emi}

    customer={k:getattr(c,k) for k in ["id","name","pan","mobile","email","address","permanent_address","current_city","gender","business_name","business_type","date_of_birth","aadhaar_masked","marital_status","customer_type","occupation","monthly_income","work_experience_years","years_in_business","average_bank_balance","primary_bank","cibil_score","foir","existing_emi","dependents","residence_ownership","residence_since","ownership_proof_name","ownership_proof_status","kyc_status","email_verified","selfie_status"]}
    loan_rows=[]
    for x in loans:
        try: disbursement_details = json.loads(x.disbursement_details) if x.disbursement_details else None
        except Exception: disbursement_details = {"raw": x.disbursement_details}
        loan_rows.append({"id":x.id,"product":x.product,"requested_amount":x.requested_amount,"eligible_amount":x.eligible_amount,"sanctioned_amount":x.sanctioned_amount,"disbursed_amount":x.disbursed_amount,"outstanding_amount":x.outstanding_amount,"monthly_emi":x.monthly_emi,"tenure_months":x.tenure_months,"interest_rate":x.interest_rate,"status":x.status,"current_stage":x.current_stage,"disbursement_details":disbursement_details,"scorecard_score":x.scorecard_score,"scorecard_max":x.scorecard_max,"scorecard_version":x.scorecard_version,"scorecard_decision":x.scorecard_decision,"scorecard_approval_percent":x.scorecard_approval_percent})
    journey_rows=[]
    for r in journey:
        try: details=json.loads(r.details or "{}")
        except Exception: details={"raw":r.details}
        journey_rows.append({"step_key":r.step_key,"step_number":r.step_number,"step_label":r.step_label,"status":r.status,"loan_id":r.loan_id,"details":details,"updated_at":str(r.updated_at) if r.updated_at else None})
    return {"customer":customer,"metrics":{"total_loans":len(loans),"total_loan_amount":sanctioned,"outstanding_amount":outstanding,"amount_paid":paid,"credit_score":c.cibil_score,"overdue_amount":overdue},"loans":loan_rows,"repayments":[{"id":r.id,"loan_id":r.loan_id,"installment":r.installment,"due_date":r.due_date,"due_amount":r.due_amount,"paid_amount":r.paid_amount,"status":r.status} for r in repayments],"documents":[{"id":d.id,"loan_id":d.loan_id,"document_type":d.document_type,"file_name":d.file_name,"verification_status":d.verification_status,"created_at":str(d.created_at) if d.created_at else None} for d in docs],"bank_analysis":bank,"bank_transactions":[{"id":t.id,"transaction_date":t.transaction_date,"amount":t.amount,"direction":t.direction,"category":t.category,"description":t.description,"reference":t.reference,"balance":t.balance} for t in transactions[:200]],"kyc_employment":{"kyc_status":c.kyc_status,"employment_type":c.occupation,"income":c.monthly_income,"work_experience_years":c.work_experience_years,"years_in_business":c.years_in_business,"residence_ownership":c.residence_ownership,"residence_since":c.residence_since,"ownership_proof_name":c.ownership_proof_name,"ownership_proof_status":c.ownership_proof_status,"emergency_contacts":[]},"risk_score":risk,"directcredit_score":latest_scored.scorecard_score if latest_scored else None,"loan_trend":{"applications":len(loans),"pending_approvals":sum(x.status in {"assessment","review"} for x in loans),"due_repayments":sum(x.status in {"repayment","active"} for x in loans),"overdue_loans":sum(x.status == "overdue" for x in loans),"completed_loans":sum(x.status in {"closed","repaid"} for x in loans)},"journey":journey_rows,"tabs":["profile","contact","bank_analysis","kyc_employment","risk_score","loan_request_eligibility"]}
