/* TEMPORARY DEMO CUSTOMER LOGIN
 * Mobile number only. No OTP. No password. No other login criteria.
 */
(function () {
  const TOKEN_KEY = 'dcCustomerAccessToken';
  const LEGACY_TOKEN_KEY = 'dcCustomerToken';
  const SESSION_KEY = 'dcCustomerId';
  const MOBILE_KEY = 'directcredit_customer_mobile';

  function base() {
    return (window.DIRECTCREDIT_API_BASE || localStorage.getItem('directcredit_api_url') || '').replace(/\/$/, '');
  }
  function api(path) { return `${base()}/api${path}`; }
  function initials(name) { return String(name || 'Customer').split(/\s+/).filter(Boolean).slice(0,2).map(x => x[0]).join('').toUpperCase() || 'CU'; }
  function money(n) { return '₹' + Number(n || 0).toLocaleString('en-IN'); }

  async function get(path, token) {
    const r = await fetch(api(path), { headers: { Accept: 'application/json', Authorization: `Bearer ${token}` } });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d?.error?.message || d?.detail || `API ${r.status}`);
    return d;
  }

  function profileFrom(c, loans, repayments, documents) {
    const loan = loans[0] || null;
    return {
      customerId: c.customer_code || `CUST${String(c.id).padStart(8,'0')}`, backendCustomerId: c.id,
      loginId: c.login_id || '', name: c.name || 'New Customer', mobile: c.mobile || '', email: c.email || '',
      address: c.address || '', permanentAddress: c.permanent_address || '', currentCity: c.current_city || '',
      gender: c.gender || '', dateOfBirth: c.date_of_birth || '', occupation: c.occupation || '',
      businessName: c.business_name || '', businessType: c.business_type || '', monthlyIncome: Number(c.monthly_income || 0),
      workExperienceYears: Number(c.work_experience_years || 0), yearsInBusiness: Number(c.years_in_business || 0),
      bank: c.primary_bank || '', averageBalance: Number(c.average_bank_balance || 0), cibil: Number(c.cibil_score || 0),
      foir: Number(c.foir || 0), existingEmi: Number(c.existing_emi || 0), score: '—', risk: 'Pending',
      activeLoans: loans.length, sanctioned: Number(loan?.sanctioned_amount || loan?.eligible_amount || 0),
      outstanding: Number(loan?.outstanding_amount || 0), emi: Number(loan?.monthly_emi || 0),
      nextDue: repayments[0]?.due_date || '—', applicationId: loan ? String(loan.id) : '—', status: loan?.status || 'New',
      journey: { done: [], current: 0 }, loans, repayments, documents
    };
  }

  function save(profile) {
    try { const all = JSON.parse(localStorage.getItem('dcCustomerProfiles') || '{}'); all[profile.customerId] = profile; localStorage.setItem('dcCustomerProfiles', JSON.stringify(all)); } catch (_) {}
  }

  async function login() {
    const button = document.getElementById('loginBtn');
    const mobile = String(document.getElementById('loginId')?.value || '').replace(/\D/g, '');
    if (!/^\d{10}$/.test(mobile)) { alert('Enter a valid 10-digit mobile number.'); return; }
    button.disabled = true; button.textContent = 'Opening Customer Portal…';
    try {
      // TEMP DEMO: backend accepts mobile only and creates/loads the customer.
      const r = await fetch(api('/auth/customer-mobile-login'), {
        method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ mobile })
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data?.error?.message || data?.detail || `Login failed (${r.status})`);
      const token = data.access_token;
      if (!token || !data.customer) throw new Error('Customer session was not returned by the server.');

      const customer = data.customer;
      const fullCustomer = await get('/customer/me', token);
      const loans = await get(`/customers/${fullCustomer.id}/loans`, token);
      const repayments = loans[0] ? await get(`/loans/${loans[0].id}/repayments`, token) : [];
      const documents = await get(`/customers/${fullCustomer.id}/documents`, token);
      const profile = profileFrom(fullCustomer, loans, repayments, documents);
      profile.mobile = customer.mobile || mobile;

      sessionStorage.setItem(TOKEN_KEY, token); sessionStorage.setItem(LEGACY_TOKEN_KEY, token);
      sessionStorage.setItem(SESSION_KEY, profile.customerId); sessionStorage.setItem(MOBILE_KEY, mobile);
      sessionStorage.setItem('dcCustomerLoggedIn', '1');
      window.currentCustomer = profile; save(profile);

      document.getElementById('loginView')?.classList.add('hidden');
      document.getElementById('portalView')?.classList.remove('hidden');
      if (typeof initPortal === 'function') initPortal(profile.customerId);
    } catch (e) { console.error(e); alert(e.message || 'Unable to open customer portal'); }
    finally { button.disabled = false; button.textContent = 'Enter Customer Portal'; }
  }

  function install() {
    const button = document.getElementById('loginBtn');
    const input = document.getElementById('loginId');
    if (!button || !input) return;
    input.placeholder = 'Enter mobile number'; input.maxLength = 10; input.inputMode = 'numeric';
    document.getElementById('loginPassword')?.remove();
    const label = document.querySelector('#loginView label'); if (label) label.childNodes[0].textContent = 'Mobile Number';
    const note = document.querySelector('#loginView .demo-note'); if (note) note.textContent = 'Temporary demo: enter mobile number only. No OTP or password required.';
    button.textContent = 'Enter Customer Portal'; button.onclick = login;
  }

  document.addEventListener('DOMContentLoaded', install);
})();
