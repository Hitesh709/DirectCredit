"""Phase 2V - Document Intelligence contract layer."""
PHASE2V_VERSION="MBL-DOCUMENT-INTELLIGENCE-2V-v1"
DOCUMENT_STATUSES=("MISSING","PENDING","VERIFIED","REJECTED","REVIEW")
REQUIRED_TYPES=("PAN","AADHAAR","SELFIE","BANK_STATEMENT","BUSINESS_PROOF","ADDRESS_PROOF")
def assess_documents(documents:list[dict])->dict:
 by={}
 for d in documents or []: by.setdefault(str(d.get("document_type") or "OTHER").upper(),[]).append(d)
 missing=[x for x in REQUIRED_TYPES if not by.get(x)]
 rejected=[x for x,rows in by.items() if any(str(r.get("verification_status","")).lower()=="rejected" for r in rows)]
 pending=[x for x,rows in by.items() if any(str(r.get("verification_status","")).lower() in {"pending","under_review"} for r in rows)]
 verified=[x for x,rows in by.items() if any(str(r.get("verification_status","")).lower()=="verified" for r in rows)]
 status="REJECTED" if rejected else ("MISSING" if missing else ("PENDING" if pending else "VERIFIED"))
 return {"version":PHASE2V_VERSION,"status":status,"missing":missing,"pending":pending,"rejected":rejected,"verified":verified,"document_count":len(documents or [])}
def contract(): return {"version":PHASE2V_VERSION,"purpose":"Document completeness and verification intelligence","required_types":list(REQUIRED_TYPES),"rules":["Do not infer authenticity from upload alone","OCR/provider results remain evidence","Low-confidence extraction requires review"]}