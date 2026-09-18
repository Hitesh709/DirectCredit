const API_BASE = (localStorage.getItem('directcredit_api_url') || window.DIRECTCREDIT_API_URL || '/api').replace(/\/$/, '');
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
async function createLoanApplication(){
  const customerId=sessionStorage.getItem(CUSTOMER_KEY);
  const amount=Number(document.getElementById('loanAmount')?.value);
  const tenure=Number(document.getElementById('loanTenure')?.value);
  const msg=document.getElementById('loanApplyMessage'), button=document.getElementById('applyLoanBtn');
  if(!customerId){setLoginMessage('Please log in again.',true);return;}
  if(!Number.isFinite(amount)||amount<5000||amount>15000){if(msg){msg.textContent='Enter an amount between ₹5,000 and ₹15,000.';msg.className='login-message error';}return;}
  if(![3,6,9,12].includes(tenure)){if(msg){msg.textContent='Select a supported tenure.';msg.className='login-message error';}return;}
  if(button){button.disabled=true;button.textContent='Creating application…';}
  if(msg){msg.textContent='';msg.className='login-message';}
  try{
    const result=await api(`/services/loan-request/${encodeURIComponent(customerId)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:'Micro Business Loan',requested_amount:amount,tenure_months:tenure})});
    if(msg){msg.textContent=`Application #${result.loan_id} created. Continue with your application profile.`;msg.className='login-message success';}
    await refreshApplications();
    await loadCustomerProfile(customerId);
    openSection('application');
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

function bind(){document.getElementById('loginBtn')?.addEventListener('click',loginWithMobile);document.getElementById('loginId')?.addEventListener('keydown',e=>{if(e.key==='Enter')loginWithMobile();});document.getElementById('showSignupBtn')?.addEventListener('click',showSignup);document.getElementById('applyLoanBtn')?.addEventListener('click',createLoanApplication);document.getElementById('refreshApplicationsBtn')?.addEventListener('click',refreshApplications);document.getElementById('cancelSignupBtn')?.addEventListener('click',hideSignup);document.getElementById('signupBtn')?.addEventListener('click',signupCustomer);document.getElementById('signupMobile')?.addEventListener('keydown',e=>{if(e.key==='Enter')signupCustomer();});document.getElementById('logoutBtn')?.addEventListener('click',logout);document.querySelectorAll('.side-nav').forEach(btn=>btn.addEventListener('click',()=>openSection(btn.dataset.section)));document.querySelectorAll('[data-open-section]').forEach(btn=>btn.addEventListener('click',()=>openSection(btn.dataset.openSection)));const customerId=sessionStorage.getItem(CUSTOMER_KEY),token=sessionStorage.getItem(TOKEN_KEY);if(customerId&&token)loadCustomerProfile(customerId).then(()=>{showPortal();openSection('home');}).catch(()=>logout());}
document.addEventListener('DOMContentLoaded',bind);
