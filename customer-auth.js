/* DirectCredit Task 1: persistent customer identity.
 * This script intentionally sits after customer-login.js so it replaces the
 * old browser-generated demo persona with a database-backed customer.
 */
(function () {
  const API_BASE = (window.DIRECTCREDIT_API_BASE || '').replace(/\/$/, '');
  const TOKEN_KEY = 'dcCustomerAccessToken';
  const SESSION_KEY = 'dcCustomerId';

  function money(n) { return '₹' + Number(n || 0).toLocaleString('en-IN'); }
  function initials(name) {
    return String(name || 'Customer').split(/\s+/).filter(Boolean).slice(0, 2)
      .map(x => x[0]).join('').toUpperCase() || 'CU';
  }

  function toPortalProfile(c) {
    return {
      customerId: c.customer_code || `CUST${String(c.id).padStart(8, '0')}`,
      backendCustomerId: c.id,
      loginId: c.login_id,
      name: c.name || 'New Customer',
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
      activeLoans: 0,
      sanctioned: 0,
      outstanding: 0,
      emi: 0,
      nextDue: '—',
      applicationId: '—',
      status: 'New',
      journey: { done: [], current: 0 },
      loans: [],
      repayments: [],
      documents: []
    };
  }

  async function loginAgainstBackend(loginId, password) {
    const response = await fetch(`${API_BASE}/api/customer/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login_id: loginId, password })
    });
    let payload = {};
    try { payload = await response.json(); } catch (_) {}
    if (!response.ok) throw new Error(payload.detail || 'Customer login failed');
    return payload;
  }

  function savePortalProfile(profile) {
    try {
      const all = JSON.parse(localStorage.getItem('dcCustomerProfiles') || '{}');
      all[profile.customerId] = profile;
      localStorage.setItem('dcCustomerProfiles', JSON.stringify(all));
    } catch (_) {}
  }

  function installLogin() {
    const button = document.getElementById('loginBtn');
    if (!button) return;
    button.onclick = async function () {
      const id = document.getElementById('loginId').value.trim();
      const password = document.getElementById('loginPassword').value.trim();
      if (!id || !password) {
        alert('Enter Customer ID and password/OTP.');
        return;
      }
      button.disabled = true;
      button.textContent = 'Signing in…';
      try {
        const result = await loginAgainstBackend(id, password);
        const profile = toPortalProfile(result.customer);
        savePortalProfile(profile);
        sessionStorage.setItem('dcCustomerLoggedIn', '1');
        sessionStorage.setItem(SESSION_KEY, profile.customerId);
        sessionStorage.setItem(TOKEN_KEY, result.access_token);
        window.currentCustomer = profile;
        if (typeof initPortal === 'function') initPortal(profile.customerId);
        else location.reload();
      } catch (error) {
        console.error(error);
        alert(error.message || 'Unable to sign in.');
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
      sessionStorage.removeItem(SESSION_KEY);
    }, true);
  }

  document.addEventListener('DOMContentLoaded', function () {
    installLogin();
    installLogout();
  });
})();
