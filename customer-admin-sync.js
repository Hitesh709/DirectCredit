/* DirectCredit: customer portal -> Admin/DB synchronization bridge. */
(function () {
  const API_BASE = (localStorage.getItem('directcredit_api_url') || window.DIRECTCREDIT_API_URL || '/api').replace(/\/$/, '');
  const STORE = 'dcCustomerProfiles';
  const STEP_DEFS = [['pan','PAN'],['aadhaar','Aadhaar OCR / Verification'],['selfie','Selfie'],['bureau','Bureau'],['profile','Profile'],['bank','Bank Statement & Our Analysis'],['documents','Other Documents'],['assessment','Loan Assessment'],['sanction','Sanction'],['customerApproval','Customer Approval'],['esign','E-Sign'],['disbursement','Disbursement'],['repayment','Repayment']];
  let lastSignature = '', busy = false;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const readProfiles = () => { try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (_) { return {}; } };
  const esc = v => String(v == null ? '' : v).replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

  function renderDisbursementFields(p) {
    if (Number(p.journey?.current || 0) !== 11) return;
    const host = document.querySelector('#stepPanel .step-body');
    if (!host || host.querySelector('#dcDisbursementDetails')) return;
    const d = p.disbursementDetails || {};
    const box = document.createElement('div'); box.id = 'dcDisbursementDetails'; box.className = 'info-box';
    box.innerHTML = `<strong>Disbursement Details</strong><div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px"><label>Disbursement Amount<input id="dcDisbAmount" type="number" min="0" value="${esc(d.amount || p.sanctioned || 0)}"></label><label>Disbursement Date<input id="dcDisbDate" type="date" value="${esc(d.date || '')}"></label><label>Bank Name<input id="dcDisbBank" value="${esc(d.bank || p.bank || '')}" placeholder="Bank name"></label><label>Account Last 4 Digits<input id="dcDisbLast4" maxlength="4" value="${esc(d.account_last4 || '')}" placeholder="1234"></label><label>UTR / Transaction Reference<input id="dcDisbUtr" value="${esc(d.utr || '')}" placeholder="UTR / reference"></label><label>Status<select id="dcDisbStatus"><option>Ready for Disbursement</option><option>Processing</option><option>Disbursed</option><option>Failed</option></select></label></div>`;
    host.insertBefore(box, host.querySelector('.step-actions') || null);
    if (d.status) document.getElementById('dcDisbStatus').value = d.status;
    const save = () => {
      p.disbursementDetails = { amount:Number(document.getElementById('dcDisbAmount').value || 0), date:document.getElementById('dcDisbDate').value || null, bank:document.getElementById('dcDisbBank').value || null, account_last4:document.getElementById('dcDisbLast4').value || null, utr:document.getElementById('dcDisbUtr').value || null, status:document.getElementById('dcDisbStatus').value };
      const profiles = readProfiles(); profiles[String(p.customerId)] = p; localStorage.setItem(STORE, JSON.stringify(profiles));
      if (window.directCreditSyncJourney) window.directCreditSyncJourney();
    };
    box.querySelectorAll('input,select').forEach(el => el.addEventListener('change', save));
  }

  async function ensureServerCustomer(p) {
    const numeric = /^\d+$/.test(String(p.serverCustomerId || p.customerId || ''));
    if (numeric) return Number(p.serverCustomerId || p.customerId);
    const payload = {name:String(p.name || p.customerId || 'New Customer').trim() || 'New Customer',pan:p.pan || null,mobile:p.mobile && p.mobile !== '—' ? p.mobile : null,email:p.email && p.email !== '—' ? p.email : null,address:p.address || null,permanent_address:p.permanentAddress || null,gender:p.gender || null,business_name:p.businessName || null,business_type:p.businessType || null,date_of_birth:p.dateOfBirth || null,occupation:p.occupation || 'Business',monthly_income:Number(p.monthlyIncome || 0),average_bank_balance:Number(p.averageBalance || 0),primary_bank:p.bank || null,cibil_score:Number(p.cibil || 0),foir:Number(p.foir || 0),existing_emi:Number(p.existingEmi || 0),customer_type:'Individual'};
    const r=await fetch(`${API_BASE}/customers`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!r.ok)throw new Error(`customer create ${r.status}`);
    const saved=await r.json();p.serverCustomerId=saved.id;p.customerId=String(saved.id);const profiles=readProfiles();profiles[String(p.customerId)]=p;localStorage.setItem(STORE,JSON.stringify(profiles));localStorage.setItem('directcredit_customer_id',String(saved.id));return Number(saved.id);
  }

  function collectSteps(p) {
    const done=Array.isArray(p.journey?.done)?p.journey.done:[], current=Number(p.journey?.current||0);
    return STEP_DEFS.map(([key,label],i)=>{
      let status=done.includes(key)?'completed':(i===current?'current':'pending');
      if(key==='pan'&&p.panStatus)status=p.panStatus.toLowerCase();if(key==='aadhaar'&&p.aadhaarStatus)status=p.aadhaarStatus.toLowerCase();if(key==='bank'&&p.bankStatus)status=p.bankStatus.toLowerCase();
      const details={customer_id:p.customerId,status,pan:key==='pan'?(p.pan||document.getElementById('cPan')?.value||null):undefined,aadhaar_file:key==='aadhaar'?(document.getElementById('cAadhaar')?.files?.[0]?.name||null):undefined,selfie_file:key==='selfie'?(document.getElementById('cSelfie')?.files?.[0]?.name||null):undefined,bank_statement_file:key==='bank'?(document.getElementById('cBank')?.files?.[0]?.name||null):undefined,document_file:key==='documents'?(document.getElementById('cDoc')?.files?.[0]?.name||null):undefined,name:p.name,dob:p.dateOfBirth,gender:p.gender,occupation:p.occupation,business_name:p.businessName,monthly_income:p.monthlyIncome,current_address:p.address,permanent_address:p.permanentAddress,bank:p.bank,average_balance:p.averageBalance,cibil:p.cibil,foir:p.foir,existing_emi:p.existingEmi,assessment_score:p.score,risk:p.risk,sanction_amount:p.sanctioned,customer_approval:key==='customerApproval'?!!document.getElementById('cConsent')?.checked:undefined,esign_status:key==='esign'?'Ready / Demo Success':undefined,disbursement:key==='disbursement'?(p.disbursementDetails||{status:'Ready for Disbursement',amount:p.sanctioned||0,bank:p.bank||null}):undefined,repayment:key==='repayment'?(p.repayments||[]):undefined};
      Object.keys(details).forEach(k=>details[k]===undefined&&delete details[k]);return{key,label,step_number:i+1,status,details};
    });
  }

  async function sync(){
    if(busy||!window.currentCustomer)return;busy=true;
    try{const p=window.currentCustomer;renderDisbursementFields(p);const id=await ensureServerCustomer(p),steps=collectSteps(p),loan=p.loans?.[0]||{};
      const payload={customer:{name:p.name,pan:p.pan||document.getElementById('cPan')?.value||null,mobile:p.mobile,email:p.email,address:p.address,permanent_address:p.permanentAddress,gender:p.gender,business_name:p.businessName,business_type:p.businessType,date_of_birth:p.dateOfBirth,occupation:p.occupation,monthly_income:Number(p.monthlyIncome||0),average_bank_balance:Number(p.averageBalance||0),primary_bank:p.bank,cibil_score:Number(p.cibil||0),foir:Number(p.foir||0),existing_emi:Number(p.existingEmi||0),kyc_status:p.aadhaarStatus||p.panStatus||'pending',selfie_status:p.selfieStatus||'pending'},loan:{requested_amount:Number(p.requestedAmount||loan.requested||p.sanctioned||1),eligible_amount:Number(p.eligibleAmount||p.sanctioned||loan.sanctioned||0),monthly_emi:Number(p.emi||loan.emi||0),sanctioned_amount:Number(p.sanctioned||loan.sanctioned||0),disbursed_amount:Number(p.disbursedAmount||p.disbursementDetails?.amount||0),outstanding_amount:Number(p.outstanding||loan.outstanding||0),interest_rate:Number(p.interestRate||0),tenure_months:Number(p.tenureMonths||12),status:p.status||'assessment',current_stage:steps.find(x=>x.status==='current')?.label||'PAN',product:loan.product||'Micro Business Loan',disbursement_details:p.disbursementDetails||{status:p.disbursementStatus||'Ready for Disbursement',amount:Number(p.disbursedAmount||p.sanctioned||0),bank:p.bank||null}},steps,documents:(p.documents||[]).map(d=>({name:d.name,file_name:d.fileName||d.name||'document',document_type:d.type||d.name||'Other Document',status:d.status||'Pending',verification_status:d.status||'pending',storage_key:d.storageKey||null})),repayments:(p.repayments||[]).map((r,i)=>({installment:Number(r.installment||i+1),due_date:r.due_date||r.date||'',due_amount:Number(r.due_amount||r.amount||0),paid_amount:Number(r.paid_amount||(r.status==='Paid'?r.amount:0)||0),status:String(r.status||'upcoming').toLowerCase()}))};
      const signature=JSON.stringify(payload);if(signature===lastSignature)return;const r=await fetch(`${API_BASE}/services/customers/${id}/journey`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!r.ok)throw new Error(`journey sync ${r.status}`);lastSignature=signature;
    }catch(e){console.warn('DirectCredit journey sync:',e.message)}finally{busy=false}
  }
  window.directCreditSyncJourney=sync;const boot=async()=>{for(let i=0;i<20&&!window.currentCustomer;i++)await sleep(500);sync();setInterval(sync,1500)};if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
