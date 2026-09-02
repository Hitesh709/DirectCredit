(() => {
  const params = new URLSearchParams(location.search);
  const customerId = params.get('customer_id') || localStorage.getItem('directcredit_customer_id') || '';
  const base = (localStorage.getItem('directcredit_api_url') || window.DIRECTCREDIT_API_URL || '/api').replace(/\/$/, '');
  const tabs = [
    ['customer-profile','♙','Customer Profile','View customer identity, contact, business and loan history.'],
    ['number-contact','☎','Number & Contact Details','Mobile, email, address and contact verification.'],
    ['bank-analysis','▣','Bank Statement Analysis','Cash flow, balances, transactions and banking behaviour.'],
    ['kyc-employment','▤','KYC & Employment Summary','KYC, occupation, business and employment information.'],
    ['risk-score','♙','Risk & Score Breakdown','Credit, risk indicators and score explanation.'],
    ['application-summary','▤','Loan Request & Eligibility','Requested amount, eligibility, offer and decision.']
  ];
  const view = document.getElementById('applicationView');
  const contextCustomer = document.getElementById('contextCustomer');
  const contextId = document.getElementById('contextId');
  const contextStatus = document.getElementById('contextStatus');

  function urlFor(file){
    const q = customerId ? `?customer_id=${encodeURIComponent(customerId)}&embedded=1` : '?embedded=1';
    return `${file}.html${q}`;
  }

  function cleanFrame(frame){
    try {
      const doc = frame.contentDocument;
      if(!doc) return;
      const style = doc.createElement('style');
      style.textContent = `
        html,body{background:#fff!important;overflow-x:hidden!important}
        body{margin:0!important;font-family:Inter,Segoe UI,Arial,sans-serif!important}
        body>.sidebar,.sidebar,.profile-tabs,.customer-profile-tabs,.page-head,.head{display:none!important}
        .content,.profile-page{margin:0!important;padding:16px!important;width:100%!important;max-width:none!important}
        .content{background:#fff!important}
      `;
      doc.head.appendChild(style);
      const height = Math.max(doc.body.scrollHeight, doc.documentElement.scrollHeight, 560);
      frame.style.height = `${Math.min(Math.max(height + 20, 560), 1800)}px`;
    } catch(e) { console.warn('Embedded application view styling failed', e); }
  }

  function activate(key){
    document.querySelectorAll('.application-tab').forEach(b => b.classList.toggle('active', b.dataset.view === key));
    const item = tabs.find(t => t[0] === key) || tabs[0];
    if(contextStatus) contextStatus.textContent = item[2];
    if(view){
      view.src = urlFor(item[0]);
      view.onload = () => cleanFrame(view);
    }
  }

  document.querySelectorAll('.application-tab').forEach(button => {
    button.addEventListener('click', () => activate(button.dataset.view));
  });

  document.getElementById('exportBtn')?.addEventListener('click', () => {
    if(view?.contentWindow) view.contentWindow.print();
  });
  document.getElementById('filterBtn')?.addEventListener('click', () => {
    const id = customerId || 'No application selected';
    alert(`Application filter\nCustomer / Application: ${id}\nUse the application list to select a record.`);
  });

  async function loadContext(){
    if(!customerId){
      if(contextCustomer) contextCustomer.textContent = 'Application';
      if(contextId) contextId.textContent = 'Select an application to view live information';
      return;
    }
    try{
      const r = await fetch(`${base}/customers/${encodeURIComponent(customerId)}/profile`, {headers:{Accept:'application/json'}});
      if(!r.ok) throw new Error(String(r.status));
      const data = await r.json();
      const c = data.customer || {};
      if(contextCustomer) contextCustomer.textContent = c.name || 'Customer';
      if(contextId) contextId.textContent = `Customer ID ${c.id || customerId}`;
      if(contextStatus) contextStatus.textContent = 'Live data';
    }catch(e){
      if(contextCustomer) contextCustomer.textContent = 'Application';
      if(contextId) contextId.textContent = `Customer ID ${customerId}`;
    }
  }

  loadContext();
  activate('bank-analysis');
})();
