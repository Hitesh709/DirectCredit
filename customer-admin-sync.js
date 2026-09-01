/* DirectCredit: customer portal -> Admin/DB synchronization bridge. */
(function () {
  const API_BASE = (localStorage.getItem('directcredit_api_url') || window.DIRECTCREDIT_API_URL || '/api').replace(/\/$/, '');
  const STORE = 'dcCustomerProfiles';
  let lastSignature = '';
  let busy = false;

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const readProfiles = () => { try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (_) { return {}; } };

  async function ensureServerCustomer(p) {
    const numeric = /^\d+$/.test(String(p.serverCustomerId || p.customerId || ''));
    if (numeric) return Number(p.serverCustomerId || p.customerId);
    const payload = {
      name: String(p.name || p.customerId || 'New Customer').trim() || 'New Customer',
      pan: p.pan || null, mobile: p.mobile && p.mobile !== '—' ? p.mobile : null,
      email: p.email && p.email !== '—' ? p.email : null, address: p.address || null,
      permanent_address: p.permanentAddress || null, gender: p.gender || null,
      business_name: p.businessName || null, business_type: p.businessType || null,
      date_of_birth: p.dateOfBirth || null, occupation: p.occupation || 'Business',
      monthly_income: Number(p.monthlyIncome || 0), average_bank_balance: Number(p.averageBalance || 0),
      primary_bank: p.bank || null, cibil_score: Number(p.cibil || 0), foir: Number(p.foir || 0),
      existing_emi: Number(p.existingEmi || 0), customer_type: 'Individual'
    };
    const r = await fetch(`${API_BASE}/customers`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (!r.ok) throw new Error(`customer create ${r.status}`);
    const saved = await r.json();
    p.serverCustomerId = saved.id;
    p.customerId = String(saved.id);
    const profiles = readProfiles(); profiles[String(p.customerId)] = p; localStorage.setItem(STORE, JSON.stringify(profiles));
    localStorage.setItem('directcredit_customer_id', String(saved.id));
    return Number(saved.id);
  }

  function collectSteps(p) {
    const done = Array.isArray(p.journey?.done) ? p.journey.done : [];
    const current = Number(p.journey?.current || 0);
    const statuses = ['panStatus','aadhaarStatus','selfieStatus'];
    return (window.customerSteps || []).map((s, i) => {
      let status = done.includes(s.key) ? 'completed' : (i === current ? 'current' : 'pending');
      if (s.key === 'pan' && p.panStatus) status = p.panStatus.toLowerCase();
      if (s.key === 'aadhaar' && p.aadhaarStatus) status = p.aadhaarStatus.toLowerCase();
      if (s.key === 'bank' && p.bankStatus) status = p.bankStatus.toLowerCase();
      const details = {
        customer_id: p.customerId,
        status,
        pan: s.key === 'pan' ? (p.pan || document.getElementById('cPan')?.value || null) : undefined,
        aadhaar_file: s.key === 'aadhaar' ? (document.getElementById('cAadhaar')?.files?.[0]?.name || null) : undefined,
        selfie_file: s.key === 'selfie' ? (document.getElementById('cSelfie')?.files?.[0]?.name || null) : undefined,
        bank_statement_file: s.key === 'bank' ? (document.getElementById('cBank')?.files?.[0]?.name || null) : undefined,
        document_file: s.key === 'documents' ? (document.getElementById('cDoc')?.files?.[0]?.name || null) : undefined,
        name: p.name, dob: p.dateOfBirth, gender: p.gender, occupation: p.occupation,
        business_name: p.businessName, monthly_income: p.monthlyIncome,
        current_address: p.address, permanent_address: p.permanentAddress,
        bank: p.bank, average_balance: p.averageBalance, cibil: p.cibil, foir: p.foir,
        existing_emi: p.existingEmi,
        assessment_score: p.score, risk: p.risk,
        sanction_amount: p.sanctioned,
        customer_approval: s.key === 'customerApproval' ? !!document.getElementById('cConsent')?.checked : undefined,
        esign_status: s.key === 'esign' ? 'Ready / Demo Success' : undefined,
        disbursement: s.key === 'disbursement' ? (p.disbursementDetails || { status: 'Ready for Disbursement', amount: p.sanctioned || 0, bank: p.bank || null }) : undefined,
        repayment: s.key === 'repayment' ? (p.repayments || []) : undefined
      };
      Object.keys(details).forEach(k => details[k] === undefined && delete details[k]);
      return { key: s.key, label: s.label, step_number: i + 1, status, details };
    });
  }

  async function sync() {
    if (busy || !window.currentCustomer) return;
    busy = true;
    try {
      const p = window.currentCustomer;
      const id = await ensureServerCustomer(p);
      const steps = collectSteps(p);
      const loan = p.loans?.[0] || {};
      const payload = {
        customer: {
          name: p.name, pan: p.pan || document.getElementById('cPan')?.value || null,
          mobile: p.mobile, email: p.email, address: p.address, permanent_address: p.permanentAddress,
          gender: p.gender, business_name: p.businessName, business_type: p.businessType,
          date_of_birth: p.dateOfBirth, occupation: p.occupation, monthly_income: Number(p.monthlyIncome || 0),
          average_bank_balance: Number(p.averageBalance || 0), primary_bank: p.bank, cibil_score: Number(p.cibil || 0),
          foir: Number(p.foir || 0), existing_emi: Number(p.existingEmi || 0),
          kyc_status: p.aadhaarStatus || p.panStatus || 'pending', selfie_status: p.selfieStatus || 'pending'
        },
        loan: {
          requested_amount: Number(p.requestedAmount || loan.requested || p.sanctioned || 1),
          eligible_amount: Number(p.eligibleAmount || p.sanctioned || loan.sanctioned || 0),
          monthly_emi: Number(p.emi || loan.emi || 0), sanctioned_amount: Number(p.sanctioned || loan.sanctioned || 0),
          disbursed_amount: Number(p.disbursedAmount || 0), outstanding_amount: Number(p.outstanding || loan.outstanding || 0),
          interest_rate: Number(p.interestRate || 0), tenure_months: Number(p.tenureMonths || 12),
          status: p.status || 'assessment', current_stage: steps.find(x => x.status === 'current')?.label || 'PAN',
          product: loan.product || 'Micro Business Loan',
          disbursement_details: p.disbursementDetails || { status: p.disbursementStatus || 'Ready for Disbursement', amount: Number(p.disbursedAmount || p.sanctioned || 0), bank: p.bank || null }
        },
        steps,
        documents: (p.documents || []).map(d => ({ name: d.name, file_name: d.fileName || d.name || 'document', document_type: d.type || d.name || 'Other Document', status: d.status || 'Pending', verification_status: d.status || 'pending', storage_key: d.storageKey || null })),
        repayments: (p.repayments || []).map((r, i) => ({ installment: Number(r.installment || i + 1), due_date: r.due_date || r.date || '', due_amount: Number(r.due_amount || r.amount || 0), paid_amount: Number(r.paid_amount || (r.status === 'Paid' ? r.amount : 0) || 0), status: String(r.status || 'upcoming').toLowerCase() }))
      };
      const signature = JSON.stringify(payload);
      if (signature === lastSignature) return;
      const r = await fetch(`${API_BASE}/services/customers/${id}/journey`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!r.ok) throw new Error(`journey sync ${r.status}`);
      lastSignature = signature;
    } catch (e) {
      console.warn('DirectCredit journey sync:', e.message);
    } finally { busy = false; }
  }

  window.directCreditSyncJourney = sync;
  const boot = async () => { for (let i = 0; i < 20 && !window.currentCustomer; i++) await sleep(500); sync(); setInterval(sync, 1500); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
