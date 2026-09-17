from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .admin_auth import get_current_admin
from .servicing_models import AccountingEntry
from .db_models import LoanRecord
from .phase2q_accounting import PHASE2Q_VERSION, validate_journal, ledger_summary, accounting_contract

router = APIRouter(prefix="/api/v1/accounting", tags=["phase-2q-accounting"])

class JournalCheck(BaseModel):
    debit: float = Field(ge=0)
    credit: float = Field(ge=0)
    tolerance: float = Field(default=0.01, ge=0)

@router.get("/contract")
def contract():
    return accounting_contract()

@router.post("/journal/check")
def journal_check(body: JournalCheck, admin=Depends(get_current_admin)):
    return {"validation": validate_journal(debit=body.debit, credit=body.credit, tolerance=body.tolerance).__dict__, "engine_version": PHASE2Q_VERSION}

@router.get("/loan/{loan_id}")
def loan_ledger(loan_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan = db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404, "loan_not_found")
    rows = db.query(AccountingEntry).filter(AccountingEntry.loan_id == loan_id).order_by(AccountingEntry.id).all()
    entries = [{"id": r.id, "account": r.account, "entry_type": r.entry_type, "reference": r.reference,
                "debit": r.debit or 0, "credit": r.credit or 0, "narration": r.narration,
                "entry_time": str(r.entry_time) if r.entry_time else None} for r in rows]
    return {"loan_id": loan_id, "customer_id": loan.customer_id, "summary": ledger_summary(entries), "entries": entries, "engine_version": PHASE2Q_VERSION}

@router.get("/control-tower")
def control_tower(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.query(AccountingEntry).all()
    summary = ledger_summary([{"debit": r.debit or 0, "credit": r.credit or 0} for r in rows])
    accounts = {}
    for r in rows:
        a = accounts.setdefault(r.account, {"debit": 0.0, "credit": 0.0, "entries": 0})
        a["debit"] += float(r.debit or 0); a["credit"] += float(r.credit or 0); a["entries"] += 1
    for a in accounts.values():
        a["debit"] = round(a["debit"], 2); a["credit"] = round(a["credit"], 2); a["balance"] = round(a["debit"] - a["credit"], 2)
    return {"summary": summary, "accounts": accounts, "engine_version": PHASE2Q_VERSION}
