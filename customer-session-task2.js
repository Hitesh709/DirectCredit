/* DirectCredit Task 2 — canonical customer session adapter.
 * The backend is the source of truth for customer identity. Browser localStorage
 * may keep a cache for UI continuity, but it is never allowed to choose another
 * customer once an authenticated session exists.
 */
(function () {
  const API_BASE = (window.DIRECTCREDIT_API_BASE || '').replace(/\/$/, '');
  const TOKEN_KEY = 'dcCustomerAccessToken';
  const SESSION_KEY = 'dcCustomerId';
  const originalInitPortal = window.initPortal;
  const originalSaveCurrentProfile = window.saveCurrentProfile;

  function token() { return sessionStorage.getItem(TOKEN_KEY) || ''; }

  async function api(path, options) {
    const headers = Object.assign({ 'Content-Type': 'application/json' }, (options && options.headers) || {});
    const t = token();
    if (t) headers.Authorization = `Bearer ${t}`;
    const response = await fetch(`${API_BASE}${path}`, Object.assign({}, options || {}, { headers }));
    let payload = {};
    try { payload = await response.json(); } catch (_) {}
    if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
    return payload;
  }

  function toPortalProfile(c) {
    return {
      customerId: c.customer_code || `CUST${String(c.id).padStart(8, '0')}`,
      backendCustomerId: c.id,
      loginId: c.login_id || '',
      name: c.name || 'New Customer', mobile: c.mobile || '', email: c.email || '',
      address: c.address || '', permanentAddress: c.permanent_address || '', currentCity: c.current_city || '',
      gender: c.gender || '', dateOfBirth: c.date_of_birth || '', occupation: c.occupation || '',
      businessName: c.business_name || '', businessType: c.business_type || '',
      monthlyIncome: Number(c.monthly_income || 0), workExperienceYears: Number(c.work_experience_years || 0),
      yearsInBusiness: Number(c.years_in_business || 0), bank: c.primary_bank || '',
      averageBalance: Number(c.average_bank_balance || 0), cibil: Number(c.cibil_score || 0),
      foir: Number(c.foir || 0), existingEmi: Number(c.existing_emi || 0), dependents: Number(c.dependents || 0),
      residenceOwnership: c.residence_ownership || '', residenceSince: c.residence_since || '',
      ownershipProofName: c.ownership_proof_name || '', ownershipProofStatus: c.ownership_proof_status || 'pending',
      pan: c.pan || '', panStatus: c.pan ? 'Entered' : 'Pending',
      aadhaarMasked: c.aadhaar_masked || '', aadhaarStatus: c.aadhaar_masked ? 'Entered' : 'Pending',
      bankStatus: c.primary_bank ? 'Entered' : 'Pending',
      score: '—', risk: 'Pending', activeLoans: 0, sanctioned: 0, outstanding: 0, emi: 0,
      nextDue: '—', applicationId: '—', status: c.kyc_status || 'New',
      journey: { done: [], current: 0 }, loans: [], repayments: [], documents: []
    };
  }

  async function refreshFromServer() {
    if (!token()) return null;
    try {
      const customer = await api('/api/customer/me');
      const profile = toPortalProfile(customer);
      window.currentCustomer = Object.assign({}, window.currentCustomer || {}, profile);
      sessionStorage.setItem(SESSION_KEY, profile.customerId);
      return profile;
    } catch (error) {
      console.error('Customer session refresh failed:', error);
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(SESSION_KEY);
      return null;
    }
  }

  window.directCreditCustomerApi = api;
  window.directCreditRefreshCustomer = refreshFromServer;

  /* Prevent the old demo persona generator from replacing the authenticated profile. */
  window.initPortal = async function (customerId) {
    if (token()) {
      const profile = await refreshFromServer();
      if (profile && typeof originalInitPortal === 'function') {
        window.currentCustomer = profile;
        return originalInitPortal(profile.customerId);
      }
    }
    return typeof originalInitPortal === 'function' ? originalInitPortal(customerId) : null;
  };

  /* Persist profile edits to the canonical database record. */
  window.saveCurrentProfile = async function () {
    if (typeof originalSaveCurrentProfile === 'function') originalSaveCurrentProfile();
    const p = window.currentCustomer;
    if (!p || !token() || !p.backendCustomerId) return;
    const payload = {
      name: p.name || 'New Customer', mobile: p.mobile || null, email: p.email || null,
      address: p.address || null, permanent_address: p.permanentAddress || null, current_city: p.currentCity || null,
      gender: p.gender || null, date_of_birth: p.dateOfBirth || null, occupation: p.occupation || 'Business',
      business_name: p.businessName || null, business_type: p.businessType || null,
      monthly_income: Number(p.monthlyIncome || 0), work_experience_years: Number(p.workExperienceYears || 0),
      years_in_business: Number(p.yearsInBusiness || 0), average_bank_balance: Number(p.averageBalance || 0),
      primary_bank: p.bank || null, cibil_score: Number(p.cibil || 0), foir: Number(p.foir || 0),
      existing_emi: Number(p.existingEmi || 0), dependents: Number(p.dependents || 0),
      residence_ownership: p.residenceOwnership || null, residence_since: p.residenceSince || null,
      ownership_proof_name: p.ownershipProofName || null, ownership_proof_status: p.ownershipProofStatus || null,
      pan: p.pan || null, aadhaar_masked: p.aadhaarMasked || null
    };
    try {
      const saved = await api(`/api/customers/${encodeURIComponent(p.backendCustomerId)}/profile`, { method: 'PATCH', body: JSON.stringify(payload) });
      const fresh = toPortalProfile(saved);
      window.currentCustomer = Object.assign({}, window.currentCustomer, fresh);
    } catch (error) {
      console.error('Customer profile save failed:', error);
    }
  };

  document.addEventListener('DOMContentLoaded', async function () {
    const profile = await refreshFromServer();
    if (profile && typeof window.hydrateCustomerUI === 'function') {
      window.hydrateCustomerUI();
      if (typeof window.renderHomeJourney === 'function') window.renderHomeJourney();
      if (typeof window.renderJourney === 'function') window.renderJourney();
      if (typeof window.renderStep === 'function') window.renderStep();
    }
  });
})();
