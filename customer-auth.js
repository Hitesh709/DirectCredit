/* DirectCredit customer demo OTP authentication.
 * Demo-only: any 4-digit numeric OTP is accepted after the mobile is registered.
 * Production must replace this with a real SMS OTP provider and strict OTP verification.
 */
(function () {
  const API_BASE = (window.DIRECTCREDIT_API_BASE || '').replace(/\/$/, '');
  const TOKEN_KEY = 'dcCustomerAccessToken';
  const LEGACY_TOKEN_KEY = 'dcCustomerToken';
  const SESSION_KEY = 'dcCustomerId';
  const MOBILE_KEY = 'directcredit_customer_mobile';

  function apiUrl(path) { return `${API_BASE}/api${path}`; }
  function normalizeMobile(value) {
    let p = String(value || '').replace(/\D/g, '');
    if (p.startsWith('91') && p.length === 12) p = p.slice(2);
    return p;
  }
  function initials(name) {
    return String(name || 'Customer').split(/\s+/).filter(Boolean).slice(0, 2)
      .map(x => x[0]).join('').toUpperCase() || 'CU';
  }
  function money(n) { return '₹' + Number(n || 0).toLocaleString('en-IN'); }

  function toPortalProfile(c, loans, repayments) {
    const loan = loans[0] || null;
    return {
      customerId: c.customer_code || `CUST${String(c.id).padStart(8, '0')}`,
      backendCustomerId: c.id,
      loginId: c.login_id,
      name: c.name || 'Customer',
      mobile: c.mobile || '',
      email: c.email || '',
      address: c.address || '',
      permanentAddress: c.permanent_address || '',
      currentCity: c.current_city || '',
      gender: c.gender || '',
      dateOfBirth: c.date_of_birth || '',
      occupation: c.occupation || '',
      businessName: c.business_name || '',
      businessType: c.business_type || '',
      monthlyIncome: Number(c.monthly_income || 0),
      workExperienceYears: Number(c.work_experience_years || 0),
      yearsInBusiness: Number(c.years_in_business || 0),
      bank: c.primary_bank || '',
      averageBalance: Number(c.average_bank_balance || 0),
      cibil: Number(c.cibil_score || 0),
      foir: Number(c.foir || 0),
      existingEmi: Number(c.existing_emi || 0),
      residenceOwnership: c.residence_ownership || '',
      residenceSince: c.residence_since || '',
      ownershipProofName: c.ownership_proof_name || '',
      ownershipProofStatus: c.ownership_proof_status || 'pending',
      panStatus: c.pan ? 'Entered' : 'Pending',
      aadhaarStatus: c.aadhaar_masked ? 'Entered' : 'Pending',
      bankStatus: c.primary_bank ? 'Entered' : 'Pending',
      score: '—',
      risk: 'Pending',
      activeLoans: loans.length,
      sanctioned: Number(loan?.sanctioned_amount || loan?.eligible_amount || 0),
      outstanding: Number(loan?.outstanding_amount || 0),
      emi: Number(loan?.monthly_emi || 0),
      nextDue: repayments[0]?.due_date || '—',
      applicationId: loan ? String(loan.id) : '—',
      status: loan?.status || 'New',
      journey: { done: [], current: 0 },
      loans,
      repayments,
      documents: []
    };
  }

  async function post(path, body) {
    const response = await fetch(apiUrl(path), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(body)
    });
    let payload = {};
    try { payload = await response.json(); } catch (_) {}
    if (!response.ok) throw new Error(payload?.error?.message || payload?.detail || 'Customer login failed');
    return payload;
  }

  async function get(path, token) {
    const response = await fetch(apiUrl(path), {
      headers: { 'Accept': 'application/json', 'Authorization': `Bearer ${token}` }
    });
    let payload = {};
    try { payload = await response.json(); } catch (_) {}
    if (!response.ok) throw new Error(payload?.error?.message || payload?.detail || `API ${response.status}`);
    return payload;
  }

  function savePortalProfile(profile) {
    try {
      const all = JSON.parse(localStorage.getItem('dcCustomerProfiles') || '{}');
      all[profile.customerId] = profile;
      localStorage.setItem('dcCustomerProfiles', JSON.stringify(all));
    } catch (_) {}
  }

  function showPortal(profile) {
    window.currentCustomer = profile;
    const login = document.getElementById('loginView');
    const portal = document.getElementById('portalView');
    if (login) login.classList.add('hidden');
    if (portal) portal.classList.remove('hidden');

    document.querySelectorAll('.customer-mini b').forEach(el => { el.textContent = profile.name || 'Customer'; });
    document.querySelectorAll('.customer-mini small').forEach(el => { el.textContent = profile.customerId || '—'; });
    const avatar = document.querySelector('.customer-mini .avatar');
    if (avatar) avatar.textContent = initials(profile.name);
    const welcome = document.querySelector('#home .welcome h2');
    if (welcome) welcome.textContent = profile.name || 'Customer';

    const metrics = [...document.querySelectorAll('#home .metrics .metric strong')];
    if (metrics[0]) metrics[0].textContent = String(profile.activeLoans || 0);
    if (metrics[1]) metrics[1].textContent = money(profile.sanctioned);
    if (metrics[2]) metrics[2].textContent = money(profile.outstanding);
    if (metrics[3]) metrics[3].textContent = money(profile.emi);

    if (typeof window.renderHomeJourney === 'function') window.renderHomeJourney();
    if (typeof window.renderJourney === 'function') window.renderJourney();
  }

  async function installLogin() {
    const button = document.getElementById('loginBtn');
    if (!button) return;
    button.onclick = async function () {
      const mobile = normalizeMobile(document.getElementById('loginId')?.value);
      const otp = String(document.getElementById('loginPassword')?.value || '').replace(/\D/g, '');
      if (!/^\d{10}$/.test(mobile)) {
        alert('Enter a valid 10-digit mobile number.');
        return;
      }
      if (!/^\d{4}$/.test(otp)) {
        alert('Enter any 4-digit OTP, for example 1234.');
        return;
      }
      button.disabled = true;
      button.textContent = 'Signing in…';
      try {
        // Register the mobile in demo mode, then verify ANY 4-digit OTP.
        await post('/services/customer/auth/request-otp', { mobile });
        const result = await post('/services/customer/auth/verify-otp', { mobile, otp });
        const token = result.access_token;
        if (!token) throw new Error('Login succeeded but no customer session was returned.');

        const customer = await get('/customer/me', token);
        const loans = await get(`/customers/${customer.id}/loans`, token);
        const repayments = loans[0] ? await get(`/loans/${loans[0].id}/repayments`, token) : [];
        const documents = await get(`/customers/${customer.id}/documents`, token);
        const profile = toPortalProfile(customer, loans, repayments);
        profile.documents = documents;

        sessionStorage.setItem(TOKEN_KEY, token);
        sessionStorage.setItem(LEGACY_TOKEN_KEY, token);
        sessionStorage.setItem(SESSION_KEY, profile.customerId);
        sessionStorage.setItem(MOBILE_KEY, mobile);
        sessionStorage.setItem('dcCustomerLoggedIn', '1');
        savePortalProfile(profile);
        showPortal(profile);
      } catch (error) {
        console.error(error);
        alert(error.message || 'Customer login failed');
      } finally {
        button.disabled = false;
        button.textContent = 'Login to Customer Portal';
      }
    };
  }

  function installLogout() {
    const button = document.getElementById('logoutBtn');
    if (!button) return;
    button.addEventListener('click', function () {
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(LEGACY_TOKEN_KEY);
      sessionStorage.removeItem(SESSION_KEY);
      sessionStorage.removeItem(MOBILE_KEY);
      sessionStorage.removeItem('dcCustomerLoggedIn');
    }, true);
  }

  document.addEventListener('DOMContentLoaded', function () {
    installLogin();
    installLogout();
  });
})();