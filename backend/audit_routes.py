"""Task 8 audit query API. Access control is intentionally deferred to Task 91 RBAC."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from .database import get_db
from .db_models import AuditEventRecord

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/events")
def list_audit_events(
    db: Session = Depends(get_db),
    customer_id: int | None = Query(default=None, gt=0),
    loan_id: int | None = Query(default=None, gt=0),
    action: str | None = Query(default=None, min_length=1, max_length=100),
    entity_type: str | None = Query(default=None, min_length=1, max_length=80),
    outcome: str | None = Query(default=None, min_length=1, max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
):
    q = db.query(AuditEventRecord)
    if customer_id is not None: q = q.filter(AuditEventRecord.customer_id == customer_id)
    if loan_id is not None: q = q.filter(AuditEventRecord.loan_id == loan_id)
    if action: q = q.filter(AuditEventRecord.action == action)
    if entity_type: q = q.filter(AuditEventRecord.entity_type == entity_type)
    if outcome: q = q.filter(AuditEventRecord.outcome == outcome)
    rows = q.order_by(AuditEventRecord.id.desc()).limit(limit).all()
    return [{
        "event_id": r.event_id, "event_time": r.event_time, "actor_type": r.actor_type,
        "actor_id": r.actor_id, "action": r.action, "entity_type": r.entity_type,
        "entity_id": r.entity_id, "customer_id": r.customer_id, "loan_id": r.loan_id,
        "request_id": r.request_id, "source": r.source, "outcome": r.outcome,
        "reason_code": r.reason_code, "details": r.details,
    } for r in rows]
