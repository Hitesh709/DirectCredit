(async()=>{
  const base=(localStorage.getItem('directcredit_api_url')||window.DIRECTCREDIT_API_URL||'/api').replace(/\/$/,'');
  const fmt=v=>'₹'+Number(v||0).toLocaleString('en-IN',{maximumFractionDigits:2});
  try{
    const r=await fetch(base+'/admin/reporting'); if(!r.ok) throw Error(r.status); const d=await r.json();
    const set=(sel,val)=>{const e=document.querySelector(sel);if(e)e.textContent=val;};
    if(window.__dcRenderDashboard) window.__dcRenderDashboard(d);
    set('#dashCredit',fmt(d.amounts.paid));
    set('#dashDebit',fmt(d.amounts.due));
    set('#dashTxn',d.repayments);
    set('#riskKyc',d.customers.kyc_verified);
    set('#riskActive',d.active_loans);
    set('#riskOverdue',d.overdue_loans);
    set('#riskRepaid',d.repaid_loans);
    set('#trendApplications',d.applications);
    set('#trendDisbursed',d.disbursed_count);
    set('#trendRejected',d.rejected);
    set('#trendRepaid',d.repaid_loans);
  }catch(e){console.warn('DirectCredit live reporting unavailable:',e.message);}
})();
