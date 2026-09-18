"""Phase 3F - Controlled experimentation."""
import hashlib
PHASE3F_VERSION="MBL-EXPERIMENTS-3F-v1"
def assign(experiment_id,subject_id,variants):
 if not variants: return {"version":PHASE3F_VERSION,"status":"INVALID","reason":"NO_VARIANTS"}
 digest=int(hashlib.sha256(f"{experiment_id}:{subject_id}".encode()).hexdigest(),16)
 return {"version":PHASE3F_VERSION,"experiment_id":experiment_id,"subject_id":subject_id,"variant":variants[digest%len(variants)],"status":"ASSIGNED"}
def contract(): return {"version":PHASE3F_VERSION,"purpose":"Controlled product and policy experimentation","rules":["Assignment is reproducible","Guardrails and monitoring are required","Experiments cannot bypass credit or legal controls"]}