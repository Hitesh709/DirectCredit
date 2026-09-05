"""Operational collection functions represented in the sample workflow.

Debit requests never move money. They create an auditable request for an
external mandate/payment provider. Receipts update the canonical repayment
ledger through the same repayment records used by customer servicing.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import CustomerRecord, LoanRecord, RepaymentRecord, CollectionAgentRecord, CollectionActionRecord
from .admin_auth import get_current_admin
from .repayment_contract import calculate_dpd, derive_status
from .servicing_models import AccountingEntry

router = APIRouter(prefix="/collection", tags=["collection-operations"])

class AgentCreate(BaseModel):
    agent_code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=160)
    mobile: str | None = Field(default=None, max_length=30)

class CollectionAction(BaseModel):
    action_type: str = Field(min_length=3, max_length=50)
    agent_id: int | None = None
    amount: float = Field(default=0, ge=0)
    reference: str | None = Field(default=None, min_length=3, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)

class Receipt(BaseModel):
    amount: float = Field(gt=0)
    reference: str = Field(min_length=3, max_length=160)
    method: str = Field(default="cash", min_length=2, max_length=40)
    agent_id: int | None = None
    notes: str | None = Field(default=None, max_length=1000)

@router.get("/agents")
def agents(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.query(CollectionAgentRecord).order_by(CollectionAgentRecord.id).all()
    return [{"id": x.id, "agent_code": x.agent_code, "name": x.name, "mobile": x.mobile, "active": bool(x.active)} for x in rows]

@router.post("/agents")
def create_agent(body: AgentCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    if db.query(CollectionAgentRecord).filter(CollectionAgentRecord.agent_code == body.agent_code.strip()).first():
        raise HTTPException(409, "agent_code_already_exists")
    row = CollectionAgentRecord(agent_code=body.agent_code.strip(), name=body.name.strip(), mobile=body.mobile, active=True)
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "agent_code": row.agent_code, "name": row.name, "mobile": row.mobile, "active": True}

def _loan(loan_id: int, db: Session):
    loan = db.get(LoanRecord, loan_id)
    if not loan: raise HTTPException(404, "loan_not_found")
    customer = db.get(CustomerRecord, loan.customer_id)
    if not customer: raise HTTPException(404, "customer_not_found")
    return loan, customer

def _agent(agent_id, db):
    if agent_id is None: return None
    agent = db.get(CollectionAgentRecord, agent_id)
    if not agent or not agent.active: raise HTTPException(422, "active_collection_agent_required")
    return agent

def _overdue(loan_id, db):
    rows = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).all()
    return round(sum(max(0, float(r.due_amount or 0) - float(r.paid_amount or 0)) for r in rows if calculate_dpd(r.due_date, r.paid_amount, r.due_amount) > 0), 2)

@router.post("/loan/{loan_id}/actions")
def create_action(loan_id: int, body: CollectionAction, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer = _loan(loan_id, db); _agent(body.agent_id, db)
    allowed = {"contact", "reminder", "promise_to_pay", "bank_check", "debit_request", "field_visit"}
    action = body.action_type.strip().lower()
    if action not in allowed: raise HTTPException(422, "unsupported_collection_action")
    overdue = _overdue(loan_id, db)
    if action == "debit_request":
        if overdue <= 0: raise HTTPException(409, "no_overdue_amount")
        if loan.status not in {"active", "overdue"}: raise HTTPException(409, "loan_not_collectable")
        if not body.reference: raise HTTPException(422, "provider_reference_required")
        status = "pending_provider"
        amount = min(body.amount or overdue, overdue)
    else:
        status = "recorded"; amount = body.amount
    row = CollectionActionRecord(loan_id=loan_id, customer_id=customer.id, agent_id=body.agent_id, action_type=action, amount=amount, reference=body.reference, status=status, notes=body.notes)
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "loan_id": loan_id, "customer_id": customer.id, "action_type": action, "amount": amount, "status": status, "overdue": overdue}

@router.post("/loan/{loan_id}/receipt")
def receipt(loan_id: int, body: Receipt, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    loan, customer = _loan(loan_id, db); _agent(body.agent_id, db)
    duplicate = db.query(CollectionActionRecord).filter(CollectionActionRecord.reference == body.reference).first()
    if duplicate: raise HTTPException(409, "collection_reference_already_processed")
    rows = db.query(RepaymentRecord).filter(RepaymentRecord.loan_id == loan_id).order_by(RepaymentRecord.installment).all()
    if not rows: raise HTTPException(409, "no_repayment_schedule")
    remaining = body.amount; allocated = 0.0
    for row in rows:
        balance = max(0.0, float(row.due_amount or 0) - float(row.paid_amount or 0))
        take = min(balance, remaining)
        if take <= 0: continue
        row.paid_amount = round(float(row.paid_amount or 0) + take, 2)
        row.payment_reference = body.reference
        row.payment_method = body.method
        row.paid_at = datetime.utcnow()
        row.status = derive_status(row.due_date, row.due_amount, row.paid_amount)
        allocated += take; remaining = round(remaining - take, 2)
        if remaining <= 0: break
    if allocated <= 0: raise HTTPException(409, "no_outstanding_repayment_balance")
    loan.outstanding_amount = round(sum(max(0, float(r.due_amount or 0) - float(r.paid_amount or 0)) for r in rows), 2)
    loan.status = "repaid" if loan.outstanding_amount <= 0 else ("overdue" if any(calculate_dpd(r.due_date, r.paid_amount, r.due_amount) > 0 for r in rows if r.paid_amount < r.due_amount) else "active")
    action = CollectionActionRecord(loan_id=loan_id, customer_id=customer.id, agent_id=body.agent_id, action_type="receipt", amount=allocated, reference=body.reference, status="posted", notes=body.notes)
    db.add(action)
    db.add(AccountingEntry(loan_id=loan_id, customer_id=customer.id, account="loan_receivable", entry_type="collection_receipt", reference=body.reference, credit=allocated, narration=f"Collection receipt via {body.method}"))
    db.commit(); db.refresh(action)
    return {"action_id": action.id, "loan_id": loan_id, "received": body.amount, "allocated": allocated, "unallocated": remaining, "outstanding_amount": loan.outstanding_amount, "status": loan.status}

@router.get("/agents/performance")
def agent_performance(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    agents = db.query(CollectionAgentRecord).all(); out=[]
    for a in agents:
        actions = db.query(CollectionActionRecord).filter(CollectionActionRecord.agent_id == a.id).all()
        receipts = [x for x in actions if x.action_type == "receipt" and x.status == "posted"]
        out.append({"agent_id": a.id, "agent_code": a.agent_code, "name": a.name, "active": bool(a.active), "actions": len(actions), "receipts": len(receipts), "collected_amount": round(sum(x.amount or 0 for x in receipts), 2), "debit_requests": sum(x.action_type == "debit_request" for x in actions), "pending_debit_requests": sum(x.action_type == "debit_request" and x.status == "pending_provider" for x in actions)})
    return sorted(out, key=lambda x: (-x["collected_amount"], x["agent_id"]))

@router.get("/loan/{loan_id}/actions")
def loan_actions(loan_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    _loan(loan_id, db)
    rows = db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id == loan_id).order_by(CollectionActionRecord.id.desc()).all()
    return [{"id": x.id, "action_type": x.action_type, "agent_id": x.agent_id, "amount": x.amount or 0, "reference": x.reference, "status": x.status, "notes": x.notes, "created_at": str(x.created_at) if x.created_at else None} for x in rows]
