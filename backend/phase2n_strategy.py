"""Phase 2N - Collections Strategy & Allocation Engine.

Deterministic, explainable work allocation. This module never posts payments and
never changes credit decisions. It produces an operational assignment plan.
"""
from dataclasses import dataclass
from typing import Optional

PHASE2N_VERSION = "MBL-COLLECTIONS-2N-v1"

BUCKET_ORDER = {"CURRENT": 0, "DPD_1_7": 1, "DPD_8_30": 2, "DPD_31_60": 3, "DPD_61_90": 4, "DPD_90_PLUS": 5}

@dataclass(frozen=True)
class AllocationDecision:
    loan_id: int
    agent_id: Optional[str]
    score: int
    strategy: str
    reason_codes: tuple[str, ...]
    sla_hours: int


def _num(value, default=0.0):
    try: return float(value or 0)
    except (TypeError, ValueError): return default


def allocation_score(*, bucket: str, overdue_amount: float, max_dpd: int,
                     agent_capacity: float = 1.0, skill_match: float = 0.0,
                     geography_match: float = 0.0, active_ptp: bool = False,
                     failed_debit: bool = False) -> int:
    """Return a bounded 0-100 operational priority score."""
    score = BUCKET_ORDER.get(bucket, 0) * 15
    amount = _num(overdue_amount)
    if amount >= 50000: score += 15
    elif amount >= 25000: score += 10
    elif amount >= 10000: score += 5
    score += min(10, max(0, int(max_dpd) // 15))
    if active_ptp: score += 8
    if failed_debit: score += 7
    score += min(10, max(0, int(skill_match)))
    score += min(10, max(0, int(geography_match)))
    # Capacity is a routing signal: overloaded agents should not receive more work.
    score -= min(15, max(0, int((1.0 - max(0.0, min(1.0, agent_capacity))) * 15)))
    return max(0, min(100, score))


def choose_strategy(*, bucket: str, mandate_active: bool, active_ptp: bool,
                    failed_debit: bool, max_dpd: int) -> str:
    if bucket == "DPD_90_PLUS": return "MANUAL_ESCALATION"
    if active_ptp: return "PTP_FOLLOW_UP"
    if mandate_active and not failed_debit and max_dpd > 0: return "AUTO_DEBIT_REVIEW"
    if bucket in {"DPD_31_60", "DPD_61_90"}: return "FIELD_VISIT_REVIEW"
    if max_dpd > 0: return "CUSTOMER_CONTACT"
    return "NO_COLLECTION_ACTION"


def sla_hours(bucket: str) -> int:
    return {"DPD_1_7": 72, "DPD_8_30": 48, "DPD_31_60": 24, "DPD_61_90": 12, "DPD_90_PLUS": 4}.get(bucket, 168)


def reason_codes(*, bucket: str, overdue_amount: float, max_dpd: int,
                 active_ptp: bool, failed_debit: bool, skill_match: float,
                 geography_match: float) -> tuple[str, ...]:
    out=[]
    if max_dpd > 0: out.append("OVERDUE")
    if max_dpd >= 31: out.append("AGING_31_PLUS_DPD")
    if max_dpd >= 90: out.append("AGING_90_PLUS_DPD")
    if _num(overdue_amount) >= 25000: out.append("MATERIAL_OVERDUE")
    if active_ptp: out.append("PTP_ACTIVE")
    if failed_debit: out.append("DEBIT_FAILED")
    if skill_match > 0: out.append("SKILL_MATCH")
    if geography_match > 0: out.append("GEOGRAPHY_MATCH")
    return tuple(out)


def build_allocation(*, loan_id: int, bucket: str, overdue_amount: float,
                     max_dpd: int, agents: list[dict], mandate_active: bool=False,
                     active_ptp: bool=False, failed_debit: bool=False) -> AllocationDecision:
    """Select the least-loaded suitable agent, with deterministic tie-breaking."""
    strategy=choose_strategy(bucket=bucket, mandate_active=mandate_active,
                             active_ptp=active_ptp, failed_debit=failed_debit,
                             max_dpd=max_dpd)
    candidates=[]
    for a in agents or []:
        capacity=max(0.0,min(1.0,_num(a.get("capacity"),1.0)))
        skill=_num(a.get("skill_match"),0)
        geo=_num(a.get("geography_match"),0)
        score=allocation_score(bucket=bucket,overdue_amount=overdue_amount,max_dpd=max_dpd,
                               agent_capacity=capacity,skill_match=skill,geography_match=geo,
                               active_ptp=active_ptp,failed_debit=failed_debit)
        candidates.append((capacity,-score,str(a.get("agent_id")),score,skill,geo))
    chosen=None
    if candidates:
        candidates.sort(key=lambda x:(x[0],x[1],x[2]))
        c=candidates[0]; chosen=(c[2],c[3],c[4],c[5])
    agent_id=chosen[0] if chosen else None
    score=chosen[1] if chosen else allocation_score(bucket=bucket,overdue_amount=overdue_amount,max_dpd=max_dpd,active_ptp=active_ptp,failed_debit=failed_debit)
    skill=chosen[2] if chosen else 0
    geo=chosen[3] if chosen else 0
    return AllocationDecision(loan_id,agent_id,score,strategy,reason_codes(bucket=bucket,overdue_amount=overdue_amount,max_dpd=max_dpd,active_ptp=active_ptp,failed_debit=failed_debit,skill_match=skill,geography_match=geo),sla_hours(bucket))


def strategy_contract():
    return {"version":PHASE2N_VERSION,"purpose":"collections strategy and workload allocation","strategies":["CUSTOMER_CONTACT","PTP_FOLLOW_UP","AUTO_DEBIT_REVIEW","FIELD_VISIT_REVIEW","MANUAL_ESCALATION","NO_COLLECTION_ACTION"],"dpd_sla_hours":{"DPD_1_7":72,"DPD_8_30":48,"DPD_31_60":24,"DPD_61_90":12,"DPD_90_PLUS":4},"principles":["deterministic and explainable","operational allocation only","never posts payments","never changes credit decisions","provider confirmation remains mandatory","customer and loan scope enforced at API boundary","capacity balancing prevents avoidable collector overload"]}
