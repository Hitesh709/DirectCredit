"""Phase 3J - Data Warehouse/Lakehouse contract and metrics layer."""
PHASE3J_VERSION="MBL-DATA-PLATFORM-3J-v1"
def dataset_contract(*,name:str,columns:list[str],source:str)->dict: return {"version":PHASE3J_VERSION,"dataset":name,"columns":columns,"source":source,"lineage_required":True,"quality_status":"UNASSESSED"}
def quality(*,rows:int,nulls:int=0,duplicates:int=0)->dict:
 r=max(0,int(rows)); return {"version":PHASE3J_VERSION,"rows":r,"nulls":int(nulls or 0),"duplicates":int(duplicates or 0),"null_rate_pct":round(int(nulls or 0)/r*100,2) if r else 0,"status":"REVIEW" if nulls or duplicates else "PASS"}
def contract(): return {"version":PHASE3J_VERSION,"purpose":"Governed analytical warehouse/lakehouse contracts","rules":["Source lineage required","Raw data is immutable by convention","Quality checks precede analytical consumption"]}