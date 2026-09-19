// Customer Portal uses the Vercel /api rewrite in production. Ignore stale localStorage API overrides so an older browser session cannot point login at a retired backend.
const API_BASE = (window.DIRECTCREDIT_API_URL || '/api').replace(/\/$/, '');
const TOKEN_KEY = 'directcredit_customer_token';
const CUSTOMER_KEY = 'directcredit_customer_id';
let currentCustomer = null;
let profileData = null;

const esc = (v) => String(v ?? '').replace(/[&<>\"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
const text = (v, fallback = 'Not available') => v !== null && v !== undefined && String(v).trim() !== '' ? String(v) : fallback;
const money = (v) => v === null || v === undefined || v === '' || Number.isNaN(Number(v)) ? 'Not available' : `₹${Number(v).toLocaleString('en-IN')}`;
const initials = (name) => String(name || 'Customer').split(/\s+/).filter(Boolean).slice(0,2).map(x => x[0]).join('').toUpperCase() || 'CU';
const statusLabel = (v) => text(v).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

async function api(path, options = {}) {
  const headers = { Accept: 'application/json', ...(options.headers || {}) };
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  let body = null; try { body = await response.json(); } catch (_) {}
  if (!response.ok) throw new Error(body?.message || body?.detail || `Request failed (${response.status})`);
  return body;
}
function setLoginMessage(message = '', error = false) { const el = document.getElementById('loginMessage'); if (!el) return; el.textContent = message; el.className = `login-message${error ? ' error' : ''}`; }
function showLogin() { document.getElementById('loginView')?.classList.remove('hidden'); document.getElementById('portalView')?.classList.add('hidden'); }
function showSignup() {
  document.getElementById('signupView')?.classList.remove('hidden');
  document.getElementById('showSignupBtn')?.classList.add('hidden');
  document.getElementById('loginBtn')?.classList.add('hidden');
  document.getElementById('loginId')?.closest('label')?.classList.add('hidden');
  document.getElementById('signupName')?.focus();
  setLoginMessage('');
}
function hideSignup() {
  document.getElementById('signupView')?.classList.add('hidden');
  document.getElementById('showSignupBtn')?.classList.remove('hidden');
  document.getElementById('loginBtn')?.classList.remove('hidden');
  document.getElementById('loginId')?.closest('label')?.classList.remove('hidden');
  setLoginMessage('');
}
function showPortal() { document.getElementById('loginView')?.classList.add('hidden'); document.getElementById('portalView')?.classList.remove('hidden'); }

function renderProfile(c, data) {
  const box = document.querySelector('.profile-data'); if (!box) return;
  const business = data?.businesses?.[0] || {};
  const bank = data?.bank_accounts?.find(x => x.is_primary) || data?.bank_accounts?.[0] || {};
  const rows = [
    ['Customer ID', c.customer_code || c.id], ['Mobile Number', c.mobile], ['Email', c.email],
    ['Address', c.address], ['Customer Type', c.customer_type], ['Occupation', c.occupation],
    ['Business Name', business.legal_name || c.business_name], ['Business Type', business.business_type || c.business_type],
    ['Monthly Income', c.monthly_income == null ? null : money(c.monthly_income)],
    ['Primary Bank', bank.bank_name || c.primary_bank], ['Average Bank Balance', c.average_bank_balance == null ? null : money(c.average_bank_balance)],
    ['CIBIL Score', c.cibil_score], ['FOIR', c.foir == null ? null : `${c.foir}%`], ['Existing EMI', c.existing_emi == null ? null : money(c.existing_emi)]
  ];
  box.innerHTML = rows.map(([k,v]) => `<div><span>${esc(k)}</span><b>${esc(text(v))}</b></div>`).join('');
}
function renderProfileSecondary(c, data) {
  const box = document.querySelector('.profile-data-secondary'); if (!box) return;
  const k = data?.kyc || {}, b = data?.businesses?.[0] || {}, r = data?.risk_profile || {};
  const rows = [
    ['KYC Status', k.status || c.kyc_status], ['PAN Verification', k.pan_status], ['Identity Verification', k.identity_status],
    ['Address Verification', k.address_status], ['Business Verification', k.business_status],
    ['Business Vintage', b.business_vintage_years == null ? null : `${b.business_vintage_years} years`],
    ['Annual Turnover', b.annual_turnover == null ? null : money(b.annual_turnover)],
    ['Residence Ownership', c.residence_ownership], ['Ownership Proof', c.ownership_proof_status],
    ['Risk Status', r.risk_status], ['Fraud Status', r.fraud_status], ['Credit Status', r.credit_status]
  ];
  box.innerHTML = rows.map(([k,v]) => `<div><span>${esc(k)}</span><b>${esc(text(v))}</b></div>`).join('');
}
function renderJourney(rows) {
  const host = document.getElementById('homeProgress'), rail = document.getElementById('journeyRail'), panel = document.getElementById('stepPanel');
  if (!rows.length) { const empty='<div class="empty-state">No application journey data has been recorded for this customer.</div>'; if(host)host.innerHTML=empty; if(rail)rail.innerHTML=empty; if(panel)panel.innerHTML='<div class="empty-state">No application step data is available.</div>'; return; }
  const sorted = [...rows].sort((a,b) => Number(a.step_number || 0) - Number(b.step_number || 0));
  const html = sorted.map((s,i) => `<div class="journey-row"><span class="num">${esc(s.step_number || i+1)}</span><div><b>${esc(text(s.step_label || s.step_key))}</b><small>${esc(statusLabel(s.status))}</small></div></div>`).join('');
  if(host) host.innerHTML=html; if(rail) rail.innerHTML=html;
  const current = sorted.find(x => ['current','pending','in_progress'].includes(String(x.status).toLowerCase())) || sorted[0];
  if(panel && current) panel.innerHTML=`<div class="step-body"><span class="eyebrow">APPLICATION STEP</span><h2>${esc(text(current.step_label || current.step_key))}</h2><p>Status: <b>${esc(statusLabel(current.status))}</b></p></div>`;
}
function renderLoans(loans) {
  const body=document.querySelector('#loans tbody'); if(!body)return;
  if(!loans.length){body.innerHTML='<tr><td colspan="6" class="empty-state">No loan records found.</td></tr>';return;}
  body.innerHTML=loans.map(l=>`<tr><td>${esc(text(l.id))}</td><td>${esc(text(l.product))}</td><td>${esc(money(l.sanctioned_amount || l.requested_amount))}</td><td>${esc(money(l.outstanding_amount))}</td><td>${esc(money(l.monthly_emi))}</td><td>${esc(statusLabel(l.status))}</td></tr>`).join('');
}
function renderRepayments(rows) {
  const body=document.querySelector('#repayment tbody'); if(!body)return;
  const paid=rows.reduce((s,r)=>s+Number(r.paid_amount||0),0), unpaid=rows.reduce((s,r)=>s+Math.max(Number(r.due_amount||0)-Number(r.paid_amount||0),0),0);
  const metrics=[...document.querySelectorAll('#repayment .metrics .metric strong')]; if(metrics[0])metrics[0].textContent=money(paid); if(metrics[1])metrics[1].textContent=money(unpaid);
  const next=rows.filter(r=>Number(r.due_amount||0)>Number(r.paid_amount||0)).sort((a,b)=>String(a.due_date).localeCompare(String(b.due_date)))[0]; if(metrics[2])metrics[2].textContent=next?money(Math.max(Number(next.due_amount||0)-Number(next.paid_amount||0),0)):'Not available';
  if(!rows.length){body.innerHTML='<tr><td colspan="5" class="empty-state">No repayment records found.</td></tr>';return;}
  body.innerHTML=rows.map(r=>`<tr><td>${esc(text(r.due_date))}</td><td>${esc(text(r.loan_id))}</td><td>${esc(money(r.paid_amount || r.due_amount))}</td><td>${esc(text(r.payment_method,'Recorded'))}</td><td>${esc(statusLabel(r.status))}</td></tr>`).join('');
}
function renderDocuments(rows) { const host=document.getElementById('documentGrid'); if(!host)return; if(!rows.length){host.innerHTML='<div class="panel empty-state">No document records found.</div>';return;} host.innerHTML=rows.map(d=>`<div class="panel doc"><b>${esc(text(d.document_type))}</b><span>${esc(text(d.file_name))}</span><mark>${esc(statusLabel(d.verification_status))}</mark></div>`).join(''); }

function renderDashboard() {
  refreshApplications();
  loadActiveApplication();
  const c=profileData?.customer||currentCustomer||{}, loans=profileData?.loans||[], repayments=profileData?.repayments||[], journey=profileData?.journey||[], metrics=profileData?.metrics||{};
  document.querySelectorAll('.customer-mini b').forEach(el=>el.textContent=text(c.name,'Customer'));
  document.querySelectorAll('.customer-mini small').forEach(el=>el.textContent=text(c.customer_code||c.id,'Not available'));
  const av=document.querySelector('.customer-mini .avatar'); if(av)av.textContent=initials(c.name);
  const status=document.getElementById('accountStatus'); if(status)status.textContent='Customer 360 Connected';
  const welcome=document.querySelector('.welcome h2'); if(welcome)welcome.textContent=text(c.name,'Customer');
  const risk=profileData?.risk_profile||{};
  const score=profileData?.directcredit_score ?? risk.risk_score ?? c.cibil_score;
  const scoreEl=document.querySelector('.welcome-score strong'), scoreStatus=document.querySelector('.welcome-score span'); if(scoreEl)scoreEl.textContent=score==null||Number(score)===0?'Not available':score; if(scoreStatus)scoreStatus.textContent=risk.risk_status?statusLabel(risk.risk_status):(score?'Profile score':'Not assessed');
  const hm=[...document.querySelectorAll('#home .metrics .metric')]; if(hm[0])hm[0].querySelector('strong').textContent=String(metrics.total_loans??loans.length); if(hm[1])hm[1].querySelector('strong').textContent=money(metrics.total_loan_amount); if(hm[2])hm[2].querySelector('strong').textContent=money(metrics.outstanding_amount);
  const next=repayments.filter(r=>Number(r.due_amount||0)>Number(r.paid_amount||0)).sort((a,b)=>String(a.due_date).localeCompare(String(b.due_date)))[0]; if(hm[3]){hm[3].querySelector('strong').textContent=next?money(Math.max(Number(next.due_amount||0)-Number(next.paid_amount||0),0)):'Not available';hm[3].querySelector('span').textContent=next?`Due ${text(next.due_date)}`:'No upcoming EMI recorded';}
  const latest=loans[0], detail=[...document.querySelectorAll('#home .latest-loan .detail-list b')]; if(detail.length){detail[0].textContent=latest?text(latest.id):'Not available';detail[1].textContent=latest?text(latest.product):'Not available';detail[2].textContent=latest?money(latest.sanctioned_amount||latest.requested_amount):'Not available';detail[3].textContent=latest?money(latest.outstanding_amount):'Not available';detail[4].textContent=latest?statusLabel(latest.status):'Not available';}
  renderJourney(journey); renderProfile(c,profileData); renderProfileSecondary(c,profileData); renderLoans(loans); renderRepayments(repayments); renderDocuments(profileData?.documents||[]);
}

async function signupCustomer(){
  const name=String(document.getElementById('signupName')?.value||'').trim();
  const mobile=String(document.getElementById('signupMobile')?.value||'').replace(/\D/g,'').slice(0,10);
  if(name.length<2){setLoginMessage('Enter your full name.',true);return;}
  if(mobile.length!==10){setLoginMessage('Enter a valid 10-digit mobile number.',true);return;}
  const button=document.getElementById('signupBtn');
  if(button){button.disabled=true;button.textContent='Creating account…';}
  setLoginMessage('');
  try{
    const result=await api('/services/api/auth/customer-register',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name,mobile})
    });
    sessionStorage.setItem(TOKEN_KEY,result.access_token);
    sessionStorage.setItem(CUSTOMER_KEY,String(result.customer.id));
    await loadCustomerProfile(result.customer.id);
    showPortal();
    openSection('home');
  }catch(err){
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(CUSTOMER_KEY);
    setLoginMessage(err.message||'Customer registration failed.',true);
  }finally{
    if(button){button.disabled=false;button.textContent='Create Customer Account';}
  }
}

async function loadCustomerProfile(customerId){ profileData=await api(`/services/api/v1/customers/${encodeURIComponent(customerId)}/360`); currentCustomer=profileData.customer; renderDashboard(); }
async function loginWithMobile(){ const input=document.getElementById('loginId'),mobile=String(input?.value||'').replace(/\D/g,'').slice(0,10); if(mobile.length!==10){setLoginMessage('Enter a valid 10-digit mobile number.',true);return;} const button=document.getElementById('loginBtn'); if(button){button.disabled=true;button.textContent='Checking customer record…';} setLoginMessage(''); try{const result=await api('/services/api/auth/customer-mobile-login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mobile})}); sessionStorage.setItem(TOKEN_KEY,result.access_token); sessionStorage.setItem(CUSTOMER_KEY,String(result.customer.id)); await loadCustomerProfile(result.customer.id); showPortal(); openSection('home');}catch(err){sessionStorage.removeItem(TOKEN_KEY);sessionStorage.removeItem(CUSTOMER_KEY);showLogin();setLoginMessage(err.message||'Customer record could not be loaded.',true);}finally{if(button){button.disabled=false;button.textContent='Enter Customer Portal';}} }
function logout(){sessionStorage.removeItem(TOKEN_KEY);sessionStorage.removeItem(CUSTOMER_KEY);currentCustomer=null;profileData=null;showLogin();}
function openSection(section){document.querySelectorAll('.customer-section').forEach(s=>s.classList.toggle('active-section',s.id===section));document.querySelectorAll('.side-nav').forEach(b=>b.classList.toggle('active',b.dataset.section===section));const titles={home:'Dashboard',application:'Apply for Loan',profile:'My Profile',loans:'My Loans',repayment:'Repayments',documents:'Documents',support:'Support'},title=document.getElementById('pageTitle');if(title)title.textContent=titles[section]||'Customer Portal';}
window.openSection=openSection;
let activeApplication = null;
let wizardIndex = 0;
const wizardSteps = [
  {key:'PAN', title:'PAN & Aadhaar', description:'Enter your identity details.', fields:'kyc'},
  {key:'PERSONAL', title:'Personal & Address', description:'Complete your personal and residence details.', fields:'personal'},
  {key:'BUSINESS', title:'Business & Banking', description:'Business profile and primary bank account.', fields:'business'},
  {key:'DOCUMENTS', title:'Documents', description:'Confirm the required evidence for this application.', fields:'documents'},
  {key:'REVIEW', title:'Final Review', description:'Review your application before submitting it for assessment.', fields:'review'}
];
async function loadActiveApplication(){
  const customerId=sessionStorage.getItem(CUSTOMER_KEY); if(!customerId)return null;
  try{const result=await api('/services/loan-request/'+encodeURIComponent(customerId)+'/active');activeApplication=result.application||null;if(activeApplication)openApplicationWizard(activeApplication);return activeApplication;}catch(_){return null;}
}
function wizardIndexForStage(stage){const s=String(stage||'PAN').toUpperCase();if(s==='PAN'||s==='AADHAAR')return 0;if(s==='PERSONAL'||s==='ADDRESS')return 1;if(s==='BUSINESS'||s==='BANKING')return 2;if(s==='DOCUMENTS')return 3;return 4;}
function openApplicationWizard(application){
  activeApplication=application;wizardIndex=wizardIndexForStage(application.current_stage);
  document.getElementById('applicationStart')?.classList.add('hidden');document.getElementById('applicationWizard')?.classList.remove('hidden');
  const ref=document.getElementById('wizardLoanRef');if(ref)ref.textContent='Application #'+application.loan_id+' · '+money(application.requested_amount)+' · '+application.tenure_months+' months';renderWizard();
}
function renderWizard(){
  const step=wizardSteps[wizardIndex],title=document.getElementById('wizardTitle'),desc=document.getElementById('wizardDescription'),body=document.getElementById('wizardBody'),progress=document.getElementById('wizardProgress');
  if(title)title.textContent=step.title;if(desc)desc.textContent=step.description;
  if(progress)progress.innerHTML=wizardSteps.map(function(s,i){return '<div class="wizard-dot '+(i<=wizardIndex?'done ':'')+(i===wizardIndex?'current':'')+'"><span>'+(i+1)+'</span><b>'+esc(s.title)+'</b></div>';}).join('');
  if(!body)return;
  if(step.fields==='kyc')body.innerHTML='<div class="form-grid"><label>PAN Number<input id="appPan" maxlength="10" placeholder="ABCDE1234F" value="'+esc(currentCustomer?.pan||'')+'"></label><label>Aadhaar Number<input id="appAadhaar" inputmode="numeric" maxlength="12" placeholder="12-digit Aadhaar number"></label></div><div class="info-note">Aadhaar is stored in masked form. Verification remains pending until required evidence/provider verification is completed.</div>';
  if(step.fields==='personal')body.innerHTML='<div class="form-grid"><label>Date of Birth<input id="appDob" type="date" value="'+esc(currentCustomer?.date_of_birth||'')+'"></label><label>Gender<select id="appGender"><option value="">Select</option><option>Male</option><option>Female</option><option>Other</option></select></label><label>Marital Status<select id="appMarital"><option value="">Select</option><option>Single</option><option>Married</option><option>Other</option></select></label><label>Current City<input id="appCity" value="'+esc(currentCustomer?.current_city||'')+'"></label><label class="full">Current Address<textarea id="appAddress" rows="3">'+esc(currentCustomer?.address||'')+'</textarea></label><label class="full">Permanent Address<textarea id="appPermanent" rows="3">'+esc(currentCustomer?.permanent_address||'')+'</textarea></label><label>Residence Ownership<select id="appOwnership"><option value="">Select</option><option>Owned</option><option>Rented</option><option>Leased</option><option>Family</option><option>Company</option><option>Other</option></select></label><label>Residence Since<input id="appResidenceSince" value="'+esc(currentCustomer?.residence_since||'')+'"></label></div>';
  if(step.fields==='business')body.innerHTML='<div class="form-grid"><label>Business Name<input id="appBusinessName" value="'+esc(currentCustomer?.business_name||'')+'"></label><label>Business Type<input id="appBusinessType" value="'+esc(currentCustomer?.business_type||'')+'"></label><label>Occupation<input id="appOccupation" value="'+esc(currentCustomer?.occupation||'Business')+'"></label><label>Monthly Income<input id="appIncome" type="number" min="0" value="'+(Number(currentCustomer?.monthly_income||0)||'')+'"></label><label>Years in Business<input id="appVintage" type="number" min="0" step="0.1" value="'+(Number(currentCustomer?.years_in_business||0)||'')+'"></label><label>Existing EMI<input id="appEmi" type="number" min="0" value="'+(Number(currentCustomer?.existing_emi||0)||'')+'"></label><label>Bank Name<input id="appBankName" placeholder="Bank name"></label><label>Account Holder Name<input id="appBankHolder" value="'+esc(currentCustomer?.name||'')+'"></label><label>Masked Account Number<input id="appAccountMasked" placeholder="XXXXXX1234"></label><label>IFSC<input id="appIfsc" maxlength="11" placeholder="ABCD0123456"></label><label>Account Type<select id="appAccountType"><option>SAVINGS</option><option>CURRENT</option></select></label></div>';
  if(step.fields==='documents')body.innerHTML='<div class="document-check-grid"><label><input type="checkbox" id="docPan"> PAN Card</label><label><input type="checkbox" id="docAadhaar"> Aadhaar</label><label><input type="checkbox" id="docBank"> Bank Statement</label><label><input type="checkbox" id="docBusiness"> Business Proof</label><label><input type="checkbox" id="docAddress"> Address Proof</label><label><input type="checkbox" id="docSelfie"> Selfie</label></div><div class="info-note">Confirm the documents you are ready to submit. The application will move to final review next.</div>';
  if(step.fields==='review')body.innerHTML='<div class="review-card review-final"><b>Application #'+esc(activeApplication?.loan_id)+'</b><span>Product: '+esc(activeApplication?.product||'Micro Business Loan')+'</span><span>Requested amount: '+money(activeApplication?.requested_amount)+'</span><span>Tenure: '+esc(activeApplication?.tenure_months)+' months</span><span>Application status: '+statusLabel(activeApplication?.status)+'</span><div class="review-confirm"><input type="checkbox" id="reviewConfirm"> <label for="reviewConfirm">I confirm that the information and documents provided are correct.</label></div></div><div class="info-note">Submitting sends the application into the DirectCredit assessment workflow. It does not itself mean the loan is approved.</div>';

  [['appGender','gender'],['appMarital','marital_status'],['appOwnership','residence_ownership']].forEach(function(x){const el=document.getElementById(x[0]);if(el&&currentCustomer?.[x[1]])el.value=currentCustomer[x[1]];});
}
async function saveWizardStep(){
  const customerId=sessionStorage.getItem(CUSTOMER_KEY),loanId=activeApplication?.loan_id,step=wizardSteps[wizardIndex],msg=document.getElementById('wizardMessage'),next=document.getElementById('wizardNextBtn');
  if(!customerId||!loanId)return;if(msg){msg.textContent='Saving…';msg.className='login-message';}if(next)next.disabled=true;
  try{
    if(step.fields==='kyc'){
      const pan=String(document.getElementById('appPan')?.value||'').trim().toUpperCase(),aadhaar=String(document.getElementById('appAadhaar')?.value||'').replace(/\D/g,'');
      if(pan.length!==10||!/^([A-Z]{5}[0-9]{4}[A-Z])$/.test(pan))throw new Error('Enter a valid PAN number.');
      if(aadhaar.length!==12)throw new Error('Enter a valid 12-digit Aadhaar number.');
      await api('/services/loan-request/'+customerId+'/'+loanId+'/kyc',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({pan:pan,aadhaar:aadhaar})});
      await api('/services/loan-request/'+customerId+'/'+loanId+'/stage',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage:'PERSONAL'})});
    }else if(step.fields==='personal'){
      const payload={date_of_birth:document.getElementById('appDob')?.value,gender:document.getElementById('appGender')?.value,marital_status:document.getElementById('appMarital')?.value,current_city:document.getElementById('appCity')?.value,address:document.getElementById('appAddress')?.value,permanent_address:document.getElementById('appPermanent')?.value,residence_ownership:document.getElementById('appOwnership')?.value,residence_since:document.getElementById('appResidenceSince')?.value};
      if(!payload.date_of_birth||!payload.gender||!payload.marital_status||!payload.current_city||!payload.address||!payload.permanent_address||!payload.residence_ownership||!payload.residence_since)throw new Error('Please complete all required personal and address fields.');
      await api('/services/customer-profile/'+customerId+'/personal',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      await api('/services/loan-request/'+customerId+'/'+loanId+'/stage',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage:'BUSINESS'})});
    }else if(step.fields==='business'){
      const payload={occupation:document.getElementById('appOccupation')?.value,customer_type:currentCustomer?.customer_type||'Individual',business_name:document.getElementById('appBusinessName')?.value,business_type:document.getElementById('appBusinessType')?.value,monthly_income:Number(document.getElementById('appIncome')?.value||0),years_in_business:Number(document.getElementById('appVintage')?.value||0),existing_emi:Number(document.getElementById('appEmi')?.value||0),primary_bank:document.getElementById('appBankName')?.value};
      if(!payload.business_name||!payload.business_type||!payload.monthly_income||!payload.years_in_business||!payload.primary_bank)throw new Error('Please complete the required business and banking fields.');
      if(!document.getElementById('appBankHolder')?.value||!document.getElementById('appAccountMasked')?.value)throw new Error('Enter the bank account holder and masked account number.');
      await api('/services/customer-profile/'+customerId+'/employment-business',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      await api('/services/loan-request/'+customerId+'/'+loanId+'/bank-account',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bank_name:payload.primary_bank,account_holder_name:document.getElementById('appBankHolder')?.value,account_number_masked:document.getElementById('appAccountMasked')?.value,ifsc:document.getElementById('appIfsc')?.value,account_type:document.getElementById('appAccountType')?.value})});
      await api('/services/loan-request/'+customerId+'/'+loanId+'/stage',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage:'DOCUMENTS'})});
    }else{
      const docs=[['PAN Card','docPan'],['Aadhaar','docAadhaar'],['Bank Statement','docBank'],['Business Proof','docBusiness'],['Address Proof','docAddress'],['Selfie','docSelfie']],selected=docs.filter(function(x){return document.getElementById(x[1])?.checked;});
      if(selected.length<4)throw new Error('Please confirm at least PAN, Aadhaar, Bank Statement and Business Proof.');
      for(const x of selected)await api('/services/loan-request/'+customerId+'/'+loanId+'/document',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({document_type:x[0].toUpperCase().replaceAll(' ','_'),file_name:x[0].replaceAll(' ','_')+'_customer_submission'})});
      await api('/services/loan-request/'+customerId+'/'+loanId+'/stage',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage:'REVIEW'})});
    }else{
      if(!document.getElementById('reviewConfirm')?.checked)throw new Error('Please confirm the application details before submitting.');
      await api('/services/loan-request/'+customerId+'/'+loanId+'/stage',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage:'ASSESSMENT'})});
      activeApplication.status='assessment';activeApplication.current_stage='ASSESSMENT';
    }
    if(wizardIndex<4){wizardIndex++;activeApplication.current_stage=wizardSteps[wizardIndex].key;renderWizard();if(msg){msg.textContent='Saved. Continue to the next step.';msg.className='login-message success';}}
    else{if(msg){msg.textContent='Application submitted for assessment. DirectCredit will continue the approved assessment workflow.';msg.className='login-message success';}if(next)next.disabled=true;}
    await loadCustomerProfile(customerId);
  }catch(err){if(msg){msg.textContent=err.message||'Unable to save this step.';msg.className='login-message error';}}
  finally{if(next&&wizardIndex<4)next.disabled=false;}
}
async function createLoanApplication(){
  const customerId=sessionStorage.getItem(CUSTOMER_KEY),amount=Number(document.getElementById('loanAmount')?.value),tenure=Number(document.getElementById('loanTenure')?.value),msg=document.getElementById('loanApplyMessage'),button=document.getElementById('applyLoanBtn');
  if(!customerId){setLoginMessage('Please log in again.',true);return;}
  const existing=await loadActiveApplication();if(existing){openApplicationWizard(existing);return;}
  if(!Number.isFinite(amount)||amount<5000||amount>15000){if(msg){msg.textContent='Enter an amount between ₹5,000 and ₹15,000.';msg.className='login-message error';}return;}
  if(![3,6,9,12].includes(tenure)){if(msg){msg.textContent='Select a supported tenure.';msg.className='login-message error';}return;}
  if(button){button.disabled=true;button.textContent='Creating application…';}
  try{
    const result=await api('/services/loan-request/'+encodeURIComponent(customerId),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:'Micro Business Loan',requested_amount:amount,tenure_months:tenure})});
    activeApplication={loan_id:result.loan_id,requested_amount:result.requested_amount,tenure_months:result.tenure_months,product:result.product,status:result.status,current_stage:result.current_stage};
    openApplicationWizard(activeApplication);await refreshApplications();
  }catch(err){if(msg){msg.textContent=err.message||'Unable to create loan application.';msg.className='login-message error';}}
  finally{if(button){button.disabled=false;button.textContent='Start Loan Application';}}
}

async function refreshApplications(){
  const customerId=sessionStorage.getItem(CUSTOMER_KEY), host=document.getElementById('applicationHistory');
  if(!customerId||!host)return;
  try{
    const rows=await api(`/services/loan-request/${encodeURIComponent(customerId)}`);
    if(!rows.length){host.innerHTML='<div class="empty-state">No loan applications yet.</div>';return;}
    host.innerHTML='<div class="application-list">'+rows.map(r=>`<div class="application-row"><div><b>Application #${esc(r.loan_id)}</b><small>${esc(text(r.product))} · ${esc(r.tenure_months)} months</small></div><div><strong>${esc(money(r.requested_amount))}</strong><span class="status-badge">${esc(statusLabel(r.status))}</span></div></div>`).join('')+'</div>';
  }catch(err){host.innerHTML='<div class="empty-state">Application data could not be loaded.</div>';}
}

function bind(){document.getElementById('loginBtn')?.addEventListener('click',loginWithMobile);document.getElementById('loginId')?.addEventListener('keydown',e=>{if(e.key==='Enter')loginWithMobile();});document.getElementById('showSignupBtn')?.addEventListener('click',showSignup);document.getElementById('applyLoanBtn')?.addEventListener('click',createLoanApplication);document.getElementById('wizardNextBtn')?.addEventListener('click',saveWizardStep);document.getElementById('wizardBackBtn')?.addEventListener('click',()=>{if(wizardIndex>0){wizardIndex--;renderWizard();}});document.getElementById('refreshApplicationsBtn')?.addEventListener('click',refreshApplications);document.getElementById('cancelSignupBtn')?.addEventListener('click',hideSignup);document.getElementById('signupBtn')?.addEventListener('click',signupCustomer);document.getElementById('signupMobile')?.addEventListener('keydown',e=>{if(e.key==='Enter')signupCustomer();});document.getElementById('logoutBtn')?.addEventListener('click',logout);document.querySelectorAll('.side-nav').forEach(btn=>btn.addEventListener('click',()=>openSection(btn.dataset.section)));document.querySelectorAll('[data-open-section]').forEach(btn=>btn.addEventListener('click',()=>openSection(btn.dataset.openSection)));const customerId=sessionStorage.getItem(CUSTOMER_KEY),token=sessionStorage.getItem(TOKEN_KEY);if(customerId&&token)loadCustomerProfile(customerId).then(()=>{showPortal();openSection('home');}).catch(()=>logout());}
document.addEventListener('DOMContentLoaded',bind);
