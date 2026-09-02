const API_BASE = (localStorage.getItem('directcredit_api_url') || window.DIRECTCREDIT_API_URL || '/api').replace(/\/$/, '');
const TOKEN_KEY = 'directcredit_customer_token';
const CUSTOMER_KEY = 'directcredit_customer_id';
let currentCustomer = null;
let profileData = null;

const esc = (v) => String(v ?? '').replace(/[&<>\"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));
const text = (v, fallback = 'Not available') => (v !== null && v !== undefined && String(v).trim() !== '' ? String(v) : fallback);
const money = (v) => (v === null || v === undefined || v === '' || Number.isNaN(Number(v)) ? 'Not available' : `₹${Number(v).toLocaleString('en-IN')}`);
const initials = (name) => String(name || 'Customer').split(/\s+/).filter(Boolean).slice(0,2).map(x => x[0]).join('').toUpperCase() || 'CU';

async function api(path, options = {}) {
  const headers = { Accept: 'application/json', ...(options.headers || {}) };
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  let body = null;
  try { body = await response.json(); } catch (_) {}
  if (!response.ok) throw new Error(body?.message || body?.detail || `Request failed (${response.status})`);
  return body;
}

function setLoginMessage(message = '', error = false) {
  const el = document.getElementById('loginMessage');
  if (!el) return;
  el.textContent = message;
  el.className = `login-message${error ? ' error' : ''}`;
}
function showLogin() { document.getElementById('loginView')?.classList.remove('hidden'); document.getElementById('portalView')?.classList.add('hidden'); }
function showPortal() { document.getElementById('loginView')?.classList.add('hidden'); document.getElementById('portalView')?.classList.remove('hidden'); }
function statusLabel(status) { return text(status, 'Not available').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()); }

function renderDashboard() {
  const c = profileData?.customer || currentCustomer || {};
  const m = profileData?.metrics || {};
  const loans = profileData?.loans || [];
  const repayments = profileData?.repayments || [];
  const journey = profileData?.journey || [];
  document.querySelectorAll('.customer-mini b').forEach(el => el.textContent = text(c.name, 'Customer'));
  document.querySelectorAll('.customer-mini small').forEach(el => el.textContent = text(c.customer_code || c.id, 'Not available'));
  const av = document.querySelector('.customer-mini .avatar'); if (av) av.textContent = initials(c.name);
  const accountStatus = document.getElementById('accountStatus'); if (accountStatus) accountStatus.textContent = 'Customer Record Found';
  const welcome = document.querySelector('.welcome h2'); if (welcome) welcome.textContent = text(c.name, 'Customer');

  const score = profileData?.directcredit_score ?? (profileData?.risk_score?.source === 'scorecard' ? profileData.risk_score.total_score : null);
  const scoreEl = document.querySelector('.welcome-score strong');
  const scoreStatus = document.querySelector('.welcome-score span');
  if (scoreEl) scoreEl.textContent = score == null ? 'Not available' : score;
  if (scoreStatus) scoreStatus.textContent = score == null ? 'Not assessed' : text(profileData.risk_score?.risk_tier, 'Assessed');

  const metrics = [...document.querySelectorAll('#home .metrics .metric')];
  if (metrics[0]) { metrics[0].querySelector('strong').textContent = String(m.total_loans ?? 0); metrics[0].querySelector('span').textContent = 'Recorded loans'; }
  if (metrics[1]) { metrics[1].querySelector('strong').textContent = money(m.total_loan_amount); metrics[1].querySelector('span').textContent = 'Recorded sanctioned amount'; }
  if (metrics[2]) { metrics[2].querySelector('strong').textContent = money(m.outstanding_amount); metrics[2].querySelector('span').textContent = 'Recorded outstanding'; }
  const next = repayments.filter(r => r.status !== 'paid' && Number(r.due_amount || 0) > Number(r.paid_amount || 0)).sort((a,b) => String(a.due_date).localeCompare(String(b.due_date)))[0];
  if (metrics[3]) { metrics[3].querySelector('strong').textContent = next ? money(Math.max(Number(next.due_amount || 0) - Number(next.paid_amount || 0), 0)) : 'Not available'; metrics[3].querySelector('span').textContent = next ? `Due ${text(next.due_date)}` : 'No upcoming EMI recorded'; }

  const latest = loans[0];
  const detail = [...document.querySelectorAll('#home .latest-loan .detail-list b')];
  if (detail.length) {
    detail[0].textContent = latest ? text(latest.id) : 'Not available';
    detail[1].textContent = latest ? text(latest.product) : 'Not available';
    detail[2].textContent = latest ? money(latest.sanctioned_amount || latest.requested_amount) : 'Not available';
    detail[3].textContent = latest ? money(latest.outstanding_amount) : 'Not available';
    detail[4].textContent = latest ? statusLabel(latest.status) : 'Not available';
  }
  renderJourney(journey); renderProfile(c); renderProfileSecondary(c, profileData); renderLoans(loans); renderRepayments(repayments); renderDocuments(profileData?.documents || []);
}

function renderJourney(rows) {
  const host = document.getElementById('homeProgress'); const rail = document.getElementById('journeyRail');
  if (!rows.length) { const empty = '<div class="empty-state">No application journey data has been recorded for this customer.</div>'; if (host) host.innerHTML = empty; if (rail) rail.innerHTML = empty; const panel = document.getElementById('stepPanel'); if (panel) panel.innerHTML = '<div class="empty-state">No application step data is available.</div>'; return; }
  const sorted = [...rows].sort((a,b) => Number(a.step_number || 0) - Number(b.step_number || 0));
  const html = sorted.map((s,i) => `<div class="journey-row"><span class="num">${esc(s.step_number || i + 1)}</span><div><b>${esc(text(s.step_label))}</b><small>${esc(statusLabel(s.status))}</small></div></div>`).join('');
  if (host) host.innerHTML = html; if (rail) rail.innerHTML = html;
  const current = sorted.find(x => String(x.status).toLowerCase() === 'current') || sorted.find(x => String(x.status).toLowerCase() === 'pending') || sorted[0];
  const panel = document.getElementById('stepPanel'); if (panel && current) panel.innerHTML = `<div class="step-body"><span class="eyebrow">APPLICATION STEP</span><h2>${esc(text(current.step_label))}</h2><p>Status: <b>${esc(statusLabel(current.status))}</b></p></div>`;
}

function renderProfile(c) {
  const box = document.querySelector('.profile-data'); if (!box) return;
  const rows = [['Customer ID', c.customer_code || c.id],['Mobile Number',c.mobile],['Email',c.email],['Address',c.address],['Business Name',c.business_name],['Business Type',c.business_type],['Customer Type',c.customer_type],['Occupation',c.occupation],['Monthly Income',c.monthly_income == null ? null : money(c.monthly_income)],['Primary Bank',c.primary_bank],['Average Bank Balance',c.average_bank_balance == null ? null : money(c.average_bank_balance)],['CIBIL Score',c.cibil_score],['FOIR',c.foir == null ? null : `${c.foir}%`],['Existing EMI',c.existing_emi == null ? null : money(c.existing_emi)]];
  box.innerHTML = rows.map(([k,v]) => `<div><span>${esc(k)}</span><b>${esc(text(v))}</b></div>`).join('');
}
function renderProfileSecondary(c, data) {
  const box = document.querySelector('.profile-data-secondary'); if (!box) return;
  const k = data?.kyc_employment || {};
  const rows = [['KYC Status',k.kyc_status],['Employment / Occupation',k.employment_type],['Monthly Income',k.income == null ? null : money(k.income)],['Work Experience',k.work_experience_years == null ? null : `${k.work_experience_years} years`],['Years in Business',k.years_in_business == null ? null : `${k.years_in_business} years`],['Residence Ownership',k.residence_ownership],['Ownership Proof',k.ownership_proof_status],['Credit Score',c.cibil_score],['FOIR',c.foir == null ? null : `${c.foir}%`],['Existing EMI',c.existing_emi == null ? null : money(c.existing_emi)]];
  box.innerHTML = rows.map(([key,value]) => `<div><span>${esc(key)}</span><b>${esc(text(value))}</b></div>`).join('');
}
function renderLoans(loans) { const body = document.querySelector('#loans tbody'); if (!body) return; if (!loans.length) { body.innerHTML = '<tr><td colspan="6" class="empty-state">No loan records found.</td></tr>'; return; } body.innerHTML = loans.map(l => `<tr><td>${esc(text(l.id))}</td><td>${esc(text(l.product))}</td><td>${esc(money(l.sanctioned_amount || l.requested_amount))}</td><td>${esc(money(l.outstanding_amount))}</td><td>${esc(money(l.monthly_emi))}</td><td>${esc(statusLabel(l.status))}</td></tr>`).join(''); }
function renderRepayments(rows) {
  const body = document.querySelector('#repayment tbody'); if (!body) return;
  const paid = rows.reduce((s,r) => s + Number(r.paid_amount || 0), 0); const unpaid = rows.reduce((s,r) => s + Math.max(Number(r.due_amount || 0) - Number(r.paid_amount || 0), 0), 0);
  const metrics = [...document.querySelectorAll('#repayment .metrics .metric strong')]; if (metrics[0]) metrics[0].textContent = money(paid); if (metrics[1]) metrics[1].textContent = money(unpaid);
  const next = rows.filter(r => Number(r.due_amount || 0) > Number(r.paid_amount || 0)).sort((a,b) => String(a.due_date).localeCompare(String(b.due_date)))[0]; if (metrics[2]) metrics[2].textContent = next ? money(Math.max(Number(next.due_amount || 0)-Number(next.paid_amount || 0),0)) : 'Not available';
  if (!rows.length) { body.innerHTML = '<tr><td colspan="5" class="empty-state">No repayment records found.</td></tr>'; return; }
  body.innerHTML = rows.map(r => `<tr><td>${esc(text(r.due_date))}</td><td>${esc(text(r.loan_id))}</td><td>${esc(money(r.paid_amount || r.due_amount))}</td><td>Recorded</td><td>${esc(statusLabel(r.status))}</td></tr>`).join('');
}
function renderDocuments(rows) { const host = document.getElementById('documentGrid'); if (!host) return; if (!rows.length) { host.innerHTML = '<div class="panel empty-state">No document records found.</div>'; return; } host.innerHTML = rows.map(d => `<div class="panel doc"><b>${esc(text(d.document_type))}</b><span>${esc(text(d.file_name))}</span><mark>${esc(statusLabel(d.verification_status))}</mark></div>`).join(''); }

async function loadCustomerProfile(customerId) { profileData = await api(`/customers/${encodeURIComponent(customerId)}/profile`); currentCustomer = profileData.customer; renderDashboard(); }
async function loginWithMobile() {
  const input = document.getElementById('loginId'); const mobile = String(input?.value || '').replace(/\D/g, '').slice(0, 10);
  if (mobile.length !== 10) { setLoginMessage('Enter a valid 10-digit mobile number.', true); return; }
  const button = document.getElementById('loginBtn'); if (button) { button.disabled = true; button.textContent = 'Checking customer record…'; } setLoginMessage('');
  try {
    const result = await api('/auth/customer-mobile-login', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mobile})});
    sessionStorage.setItem(TOKEN_KEY, result.access_token); sessionStorage.setItem(CUSTOMER_KEY, String(result.customer.id));
    await loadCustomerProfile(result.customer.id); showPortal(); openSection('home');
  } catch (err) { sessionStorage.removeItem(TOKEN_KEY); sessionStorage.removeItem(CUSTOMER_KEY); showLogin(); setLoginMessage(err.message || 'Customer record could not be loaded.', true); }
  finally { if (button) { button.disabled = false; button.textContent = 'Enter Customer Portal'; } }
}
function logout() { sessionStorage.removeItem(TOKEN_KEY); sessionStorage.removeItem(CUSTOMER_KEY); currentCustomer = null; profileData = null; showLogin(); }
function openSection(section) { document.querySelectorAll('.customer-section').forEach(s => s.classList.toggle('active-section', s.id === section)); document.querySelectorAll('.side-nav').forEach(b => b.classList.toggle('active', b.dataset.section === section)); const titles={home:'Dashboard',application:'Loan Application',profile:'My Profile',loans:'My Loans',repayment:'Repayments',documents:'Documents',support:'Support'}; const title=document.getElementById('pageTitle'); if(title) title.textContent=titles[section]||'Customer Portal'; }
window.openSection = openSection;
function bind() {
  document.getElementById('loginBtn')?.addEventListener('click', loginWithMobile); document.getElementById('loginId')?.addEventListener('keydown', e => { if(e.key==='Enter') loginWithMobile(); }); document.getElementById('logoutBtn')?.addEventListener('click', logout);
  document.querySelectorAll('.side-nav').forEach(btn => btn.addEventListener('click', () => openSection(btn.dataset.section))); document.querySelectorAll('[data-open-section]').forEach(btn => btn.addEventListener('click', () => openSection(btn.dataset.openSection)));
  const mobile=sessionStorage.getItem(CUSTOMER_KEY), token=sessionStorage.getItem(TOKEN_KEY); if(mobile && token) loadCustomerProfile(mobile).then(()=>{showPortal();openSection('home');}).catch(()=>logout());
}
document.addEventListener('DOMContentLoaded', bind);
