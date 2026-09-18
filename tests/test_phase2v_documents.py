from backend.phase2v_documents import assess_documents,contract
def test_contract(): assert contract()['version']=='MBL-DOCUMENT-INTELLIGENCE-2V-v1'
def test_missing(): assert assess_documents([])['status']=='MISSING'
def test_verified(): assert assess_documents([{'document_type':x,'verification_status':'verified'} for x in ('PAN','AADHAAR','SELFIE','BANK_STATEMENT','BUSINESS_PROOF','ADDRESS_PROOF')])['status']=='VERIFIED'