import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import LoanRecord, RepaymentRecord, CollectionActionRecord, CustomerRecord
from .admin_auth import get_current_admin
from .phase2m_control_tower import PHASE2M_VERSION, loan_metrics, aggregate, control_tower_contract
from .phase2j_collections_intelligence import build_priority, collection_bucket, overdue_amount

router=APIRouter(prefix="/api/v1/control-tower",tags=["phase-2m-control-tower"])


def _loan_rows(loan_id,db):
    rows=db.query(RepaymentRecord).filter(RepaymentRecord.loan_id==loan_id).all()
    actions=db.query(CollectionActionRecord).filter(CollectionActionRecord.loan_id==loan_id).all()
    return rows,actions

@router.get("/contract")
def contract(): return control_tower_contract()

@router.get("/summary")
def summary(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    metrics=[]
    for loan in db.query(LoanRecord).filter(LoanRecord.status.in_(["active","overdue","closed","repaid"])).all():
        rows,actions=_loan_rows(loan.id,db); m=loan_metrics(rows,actions); m.update({"loan_id":loan.id,"customer_id":loan.customer_id}); metrics.append(m)
    result=aggregate(metrics); result["engine_version"]=PHASE2M_VERSION
    return result

@router.get("/loans")
def loans(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    out=[]
    for loan in db.query(LoanRecord).filter(LoanRecord.status.in_(["active","overdue"])).all():
        rows,actions=_loan_rows(loan.id,db); m=loan_metrics(rows,actions)
        overdue,max_dpd=overdue_amount(rows); bucket=collection_bucket(max_dpd); p=build_priority(bucket,overdue,max_dpd)
        out.append({"loan_id":loan.id,"customer_id":loan.customer_id,"dpd":max_dpd,"bucket":bucket,"overdue_amount":overdue,"priority_score":p.score,"urgency":p.urgency,**m})
    return sorted(out,key=lambda x:(-x["priority_score"],-x["overdue_amount"],x["loan_id"]))

@router.get("/agents")
def agents(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    rows=db.query(CollectionActionRecord).filter(CollectionActionRecord.action_type.in_(["agent_assignment","collection_call","field_visit"])).all()
    stats={}
    for r in rows:
        try: details=json.loads(r.notes or "{}")
        except Exception: details={}
        aid=details.get("agent_id")
        if aid is None: continue
        s=stats.setdefault(str(aid),{"agent_id":aid,"assignments":0,"calls":0,"field_visits":0})
        if r.action_type=="agent_assignment": s["assignments"]+=1
        elif r.action_type=="collection_call": s["calls"]+=1
        elif r.action_type=="field_visit": s["field_visits"]+=1
    return sorted(stats.values(),key=lambda x:(-x["assignments"],x["agent_id"]))

@router.get("/dpd-buckets")
def dpd_buckets(db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    buckets={x:{"loan_count":0,"overdue_amount":0.0} for x in ["CURRENT","DPD_1_7","DPD_8_30","DPD_31_60","DPD_61_90","DPD_90_PLUS"]}
    for loan in db.query(LoanRecord).filter(LoanRecord.status.in_(["active","overdue"])).all():
        rows,_=_loan_rows(loan.id,db); overdue,max_dpd=overdue_amount(rows); bucket=collection_bucket(max_dpd)
        if overdue>0:
            buckets[bucket]["loan_count"]+=1; buckets[bucket]["overdue_amount"]=round(buckets[bucket]["overdue_amount"]+overdue,2)
    return buckets

@router.get("/loan/{loan_id}")
def loan_detail(loan_id:int,db:Session=Depends(get_db),admin=Depends(get_current_admin)):
    loan=db.get(LoanRecord,loan_id)
    if not loan: raise HTTPException(404,"loan_not_found")
    rows,actions=_loan_rows(loan_id,db); m=loan_metrics(rows,actions); overdue,max_dpd=overdue_amount(rows); bucket=collection_bucket(max_dpd); p=build_priority(bucket,overdue,max_dpd)
    return {"loan_id":loan.id,"customer_id":loan.customer_id,"bucket":bucket,"dpd":max_dpd,"priority_score":p.score,"urgency":p.urgency,**m,"engine_version":PHASE2M_VERSION}
