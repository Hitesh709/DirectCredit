(() => {
  const app = document.getElementById('app');
  const id = new URLSearchParams(location.search).get('customer_id') || localStorage.getItem('directcredit_customer_id') || '';
  const base = (localStorage.getItem('directcredit_api_url') || window.DIRECTCREDIT_API_URL || '/api').replace(/\/$/, '');
  const money = v => Number(v || 0).toLocaleString('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0});
  const esc = v => String(v ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const rows = obj => Object.entries(obj).map(([k,v]) => `<div class="row"><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join('');
  async function load(){
    if(!id){app.innerHTML='<div class="state"><h2>No application selected</h2><p>Select a customer/application from the Applications workflow. No demo customer data is displayed.</p></div>';return;}
    try{
      const [profileRes, loansRes] = await Promise.all([
        fetch(`${base}/customers/${encodeURIComponent(id)}/profile`,{headers:{Accept:'application/json'}}),
        fetch(`${base}/customers/${encodeURIComponent(id)}/loans`,{headers:{Accept:'application/json'}})
      ]);
      if(!profileRes.ok || !loansRes.ok) throw new Error('Live application data unavailable');
      const profile = await profileRes.json();
      const loansPayload = await loansRes.json();
      const c = profile.customer || {};
      const loans = Array.isArray(loansPayload) ? loansPayload : (loansPayload.loans || []);
      const latest = loans[0] || {};
      const requested = latest.requested_amount ?? latest.sanctioned_amount ?? 0;
      const eligible = latest.eligible_amount ?? latest.sanctioned_amount ?? 0;
      const status = latest.status || 'pending';
      app.innerHTML = `<div class="grid">
        <div class="card"><small>Requested Amount</small><strong>${money(requested)}</strong></div>
        <div class="card"><small>Eligible / Sanctioned</small><strong>${money(eligible)}</strong></div>
        <div class="card"><small>Tenure</small><strong>${esc(latest.tenure_months ? latest.tenure_months+' Months' : '—')}</strong></div>
        <div class="card"><small>Decision</small><strong><span class="status">${esc(status)}</span></strong></div>
      </div>
      <section class="section"><h3>APPLICATION DETAILS</h3><div class="rows">${rows({'Customer':c.name || '—','Customer ID':c.id || id,'Loan Reference':latest.id || '—','Loan Product':latest.product || '—','Purpose':latest.purpose || '—','Created':latest.created_at ? new Date(latest.created_at).toLocaleString('en-IN') : '—','Monthly EMI':latest.monthly_emi != null ? money(latest.monthly_emi) : '—','Interest Rate':latest.interest_rate != null ? `${latest.interest_rate}% P.A.` : '—'})}</div></section>
      <section class="section"><h3>ELIGIBILITY &amp; REPAYMENT CAPACITY</h3><div class="rows">${rows({'Monthly Income':c.monthly_income != null ? money(c.monthly_income) : '—','Existing EMI':c.existing_emi != null ? money(c.existing_emi) : '—','FOIR':c.foir != null ? `${Number(c.foir).toFixed(2)}%` : '—','CIBIL Score':c.cibil_score ?? '—','Average Bank Balance':c.average_bank_balance != null ? money(c.average_bank_balance) : '—','Business Vintage':c.years_in_business != null ? `${c.years_in_business} Years` : '—'})}</div></section>
      <section class="section"><h3>LOAN PROCESS</h3><p style="margin:0;color:#69778d;font-size:11px">Application → KYC → Bank Analysis → Risk &amp; Score → Eligibility → Sanction → Disbursement</p></section>`;
    }catch(e){app.innerHTML='<div class="state"><h2>Live application data unavailable</h2><p>Connect the DirectCredit API or select an existing application. No demo values are shown.</p></div>';}
  }
  load();
})();
