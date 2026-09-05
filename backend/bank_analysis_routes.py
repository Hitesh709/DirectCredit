"""Bank statement transaction ingestion and analysis contracts."""
from collections import defaultdict, Counter
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_current_customer
from .admin_auth import get_current_admin
from .db_models import CustomerRecord, BankTransactionRecord

router = APIRouter(prefix="/bank-analysis", tags=["bank-analysis"])

class BankTransaction(BaseModel):
    transaction_date: str = Field(min_length=8, max_length=20)
    amount: float = Field(gt=0)
    direction: str = Field(min_length=6, max_length=10)
    category: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    reference: str | None = Field(default=None, max_length=160)
    balance: float | None = None
    loan_id: int | None = None

class BankBatch(BaseModel):
    transactions: list[BankTransaction] = Field(min_length=1, max_length=5000)


def _customer(customer_id, claims, db):
    if int(claims.get("user_id", -1)) != int(customer_id): raise HTTPException(403, "customer_scope_forbidden")
    c = db.get(CustomerRecord, customer_id)
    if not c: raise HTTPException(404, "customer_not_found")
    return c

@router.post("/{customer_id}/transactions")
def ingest_customer_transactions(customer_id: int, body: BankBatch, db: Session = Depends(get_db), claims=Depends(get_current_customer)):
    _customer(customer_id, claims, db)
    rows=[]
    for item in body.transactions:
        direction=item.direction.strip().lower()
        if direction not in {"credit", "debit"}: raise HTTPException(422, "direction_must_be_credit_or_debit")
        rows.append(BankTransactionRecord(customer_id=customer_id, loan_id=item.loan_id, transaction_date=item.transaction_date, amount=item.amount, direction=direction, category=item.category, description=item.description, reference=item.reference, balance=item.balance, source="customer_statement"))
    db.add_all(rows); db.commit()
    return {"customer_id": customer_id, "inserted": len(rows), "status": "recorded"}

@router.get("/{customer_id}/transactions")
def get_customer_transactions(customer_id: int, db: Session = Depends(get_db), claims=Depends(get_current_customer)):
    _customer(customer_id, claims, db)
    rows=db.query(BankTransactionRecord).filter(BankTransactionRecord.customer_id==customer_id).order_by(BankTransactionRecord.transaction_date.desc(),BankTransactionRecord.id.desc()).limit(5000).all()
    return [{"id":x.id,"transaction_date":x.transaction_date,"amount":x.amount,"direction":x.direction,"category":x.category,"description":x.description,"reference":x.reference,"balance":x.balance,"loan_id":x.loan_id} for x in rows]

@router.get("/{customer_id}/summary")
def bank_summary(customer_id:int, db:Session=Depends(get_db), claims=Depends(get_current_customer)):
    _customer(customer_id, claims, db)
    rows=db.query(BankTransactionRecord).filter(BankTransactionRecord.customer_id==customer_id).all()
    monthly=defaultdict(lambda:{"credits":0.0,"debits":0.0,"transactions":0,"average_balance":None})
    balances=defaultdict(list); cats=Counter()
    for x in rows:
        m=str(x.transaction_date)[:7]; monthly[m]["transactions"]+=1
        if x.direction=="credit": monthly[m]["credits"]+=x.amount or 0
        else: monthly[m]["debits"]+=x.amount or 0
        if x.balance is not None: balances[m].append(x.balance)
        if x.category: cats[x.category]+=1
    for m,v in monthly.items(): v["credits"]=round(v["credits"],2);v["debits"]=round(v["debits"],2);v["average_balance"]=round(sum(balances[m])/len(balances[m]),2) if balances[m] else None
    return {"customer_id":customer_id,"transactions":len(rows),"credits":round(sum(x.amount for x in rows if x.direction=="credit"),2),"debits":round(sum(x.amount for x in rows if x.direction=="debit"),2),"negative_balance_count":sum(x.balance is not None and x.balance<0 for x in rows),"top_categories":[{"category":k,"count":v} for k,v in cats.most_common(10)],"monthly": [{"month":m,**v} for m,v in sorted(monthly.items())]}

@router.post("/admin/{customer_id}/transactions")
def ingest_admin_transactions(customer_id:int, body:BankBatch, db:Session=Depends(get_db), admin=Depends(get_current_admin)):
    if not db.get(CustomerRecord,customer_id): raise HTTPException(404,"customer_not_found")
    rows=[]
    for item in body.transactions:
        direction=item.direction.strip().lower()
        if direction not in {"credit","debit"}: raise HTTPException(422,"direction_must_be_credit_or_debit")
        rows.append(BankTransactionRecord(customer_id=customer_id,loan_id=item.loan_id,transaction_date=item.transaction_date,amount=item.amount,direction=direction,category=item.category,description=item.description,reference=item.reference,balance=item.balance,source="admin_import"))
    db.add_all(rows); db.commit()
    return {"customer_id":customer_id,"inserted":len(rows),"status":"recorded"}
