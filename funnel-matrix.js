(()=>{
  const tabs=[...document.querySelectorAll('.fm-tab')];
  const panels=[...document.querySelectorAll('.fm-view')];
  function open(view){
    tabs.forEach(x=>x.classList.toggle('active',x.dataset.view===view));
    panels.forEach(x=>x.classList.toggle('active',x.dataset.panel===view));
    history.replaceState(null,'','#'+view);
  }
  tabs.forEach(b=>b.addEventListener('click',()=>open(b.dataset.view)));
  const initial=(location.hash||'#loan').slice(1);
  open(tabs.some(x=>x.dataset.view===initial)?initial:'loan');
  document.getElementById('fmRefresh')?.addEventListener('click',()=>location.reload());
  document.getElementById('fmPrint')?.addEventListener('click',()=>window.print());

  const host=document.getElementById('registrationUsers');
  async function loadReporting(){
    if(!window.DirectCreditData){
      await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='admin-data.js?v=20260927.1';s.onload=resolve;s.onerror=reject;document.head.appendChild(s);});
    }
    return window.DirectCreditData.reporting();
  }
  async function renderUsers(){
    try{
      const report=await loadReporting();
      const demo=window.DirectCreditData.demoCustomers||[];
      let rows=demo.map(u=>({id:u.id,customer_code:u.customer_code,name:u.name,mobile:u.mobile,business_name:u.business_name,customer_type:u.customer_type,kyc_status:u.kyc_status,status:'active'}));
      if(window.DirectCreditData.loans){
        try{
          const liveLoans=await window.DirectCreditData.loans();
          const ids=[...new Set(liveLoans.map(x=>Number(x.customer_id)).filter(Boolean))];
          if(ids.length){
            const live=await Promise.all(ids.map(id=>window.DirectCreditData.customer(id).catch(()=>null)));
            rows=live.filter(x=>x&&x.customer).map(x=>{const c=x.customer;return {id:c.id,customer_code:c.customer_code,name:c.name,mobile:c.mobile,business_name:c.business_name,customer_type:c.customer_type,kyc_status:c.kyc_status,status:c.status||'active'};});
          }
        }catch(_){}
      }
      const livePreferred=report.customers?.total && report.source!=='demo';
      host.innerHTML=`<div class="fm-users-head"><div><h2>Registration & Users</h2><p>${livePreferred?'Live customer registration master':'Demo customer registration set — used because live reporting is unavailable'}</p></div></div>
      <div class="fm-user-kpis"><div class="fm-user-kpi"><small>TOTAL REGISTERED USERS</small><strong>${livePreferred?report.customers.total:rows.length}</strong></div><div class="fm-user-kpi"><small>ACTIVE USERS</small><strong>${livePreferred?report.customers.active:rows.length}</strong></div><div class="fm-user-kpi"><small>KYC VERIFIED</small><strong>${livePreferred?report.customers.kyc_verified:rows.filter(x=>String(x.kyc_status).toLowerCase()==='verified').length}</strong></div><div class="fm-user-kpi"><small>APPLICATIONS</small><strong>${report.applications||0}</strong></div></div>
      <div class="fm-user-table"><table><thead><tr><th>CUSTOMER ID</th><th>CUSTOMER CODE</th><th>NAME</th><th>MOBILE</th><th>BUSINESS</th><th>TYPE</th><th>KYC STATUS</th><th>STATUS</th></tr></thead><tbody>${rows.length?rows.map(u=>`<tr><td>${esc(u.id)}</td><td>${esc(u.customer_code)}</td><td>${esc(u.name)}</td><td>${esc(u.mobile)}</td><td>${esc(u.business_name)}</td><td>${esc(u.customer_type)}</td><td>${esc(u.kyc_status)}</td><td><span class="fm-pill">${esc(u.status||'active')}</span></td></tr>`).join(''):'<tr><td colspan="8">No registered users found.</td></tr>'}</tbody></table></div>`;
    }catch(err){
      host.innerHTML='<div class="fm-empty"><strong>Registration & Users unavailable</strong><p>Unable to load live or demo reporting data.</p></div>';
    }
  }
  renderUsers();
})();