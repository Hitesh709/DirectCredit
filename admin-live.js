(async()=>{
  const base=(localStorage.getItem('directcredit_api_url')||window.DIRECTCREDIT_API_URL||'/api').replace(/\/$/,'');
  const fmt=v=>'₹'+Number(v||0).toLocaleString('en-IN',{maximumFractionDigits:2});
  try{
    const r=await fetch(base+'/admin/reporting'); if(!r.ok) throw Error(r.status); const d=await r.json();
    const set=(sel,val)=>{const e=document.querySelector(sel);if(e)e.textContent=val;};
    if(window.__dcRenderDashboard) window.__dcRenderDashboard(d);
    set('#dashCredit',fmt(d.amounts.due)); set('#dashDebit',fmt(d.amounts.paid)); set('#dashTotalCredits',fmt(d.amounts.paid)); set('#dashTotalDebits',fmt(d.amounts.due)); set('#dashTxn',d.repayments);
    const risk=document.querySelector('#risk .scoreHero strong'); if(risk) risk.textContent='—';
    const riskText=document.querySelector('#risk .scoreHero span'); if(riskText) riskText.textContent='Live score available per customer record';
    const trendCards=document.querySelectorAll('#trend .card strong'); if(trendCards.length>=4){trendCards[0].textContent=d.applications;trendCards[1].textContent=d.disbursed_count;trendCards[2].textContent=d.rejected;trendCards[3].textContent=d.repaid_loans;}
  }catch(e){console.warn('DirectCredit live reporting unavailable:',e.message);}
})();
