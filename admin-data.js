window.DirectCreditData = (() => {
  const base = (localStorage.getItem('directcredit_api_url') || window.DIRECTCREDIT_API_URL || '/api').replace(/\/$/, '');
  async function reporting(){
    const r = await fetch(`${base}/admin/reporting`, {headers:{Accept:'application/json'}});
    if(!r.ok) throw new Error(`Reporting API ${r.status}`);
    return r.json();
  }
  async function customer(id){
    const r = await fetch(`${base}/customers/${encodeURIComponent(id)}`, {headers:{Accept:'application/json'}});
    if(!r.ok) throw new Error(`Customer API ${r.status}`);
    return r.json();
  }
  async function loans(){
    const r = await fetch(`${base}/admin/loans`, {headers:{Accept:'application/json'}});
    if(!r.ok) throw new Error(`Loans API ${r.status}`);
    return r.json();
  }
  return {base, reporting, customer, loans};
})();
