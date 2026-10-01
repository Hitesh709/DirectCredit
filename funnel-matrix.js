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

  const host=document.getElementById('registrationUsers');
  const esc=v=>String(v??'—').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const money=v=>'₹'+Number(v||0).toLocaleString('en-IN',{maximumFractionDigits:0});
  async function loadReporting(){
    if(!window.DirectCreditData){
      await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='admin-data.js?v=20261001.16';s.onload=resolve;s.onerror=reject;document.head.appendChild(s);});
    }
    return window.DirectCreditData.reporting();
  }
  async function renderUsers(){
    host.innerHTML='<div class="fm-loading">Loading registration & user data…</div>';
    try{
      const report=await loadReporting();
      const demo=window.DirectCreditData.demoCustomers||[];
      let records=Array.isArray(report.customer_records)?report.customer_records:[];
      const isDemo=report.source==='demo';
      if(isDemo || !records.length){
        records=demo.map(u=>({
          customer_id:u.id,customer_code:u.customer_code,customer_name:u.name,mobile:u.mobile,
          business_name:u.business_name,customer_type:u.customer_type,kyc_status:u.kyc_status,
          city:u.current_city,status:u.loan?.status||'active'
        }));
      }
      const total=isDemo?10:Number(report.customers?.total||records.length);
      const active=isDemo?9:Number(report.customers?.active||0);
      const kyc=isDemo?8:Number(report.customers?.kyc_verified||0);
      const applications=Number(report.applications||0);
      host.innerHTML=`
        <div class="fm-users-head">
          <div><h2>Registration &amp; Users</h2><p>${isDemo?'Demo customer registration set — reporting fallback is active':'Live customer registration master'}</p></div>
          <span class="fm-source-badge">${isDemo?'DEMO TEST DATA':'LIVE DATABASE'}</span>
        </div>
        <div class="fm-user-kpis">
          <div class="fm-user-kpi"><small>TOTAL REGISTERED USERS</small><strong>${total}</strong><span>Customer master</span></div>
          <div class="fm-user-kpi"><small>ACTIVE USERS</small><strong>${active}</strong><span>Current active profiles</span></div>
          <div class="fm-user-kpi"><small>KYC VERIFIED</small><strong>${kyc}</strong><span>Verified customers</span></div>
          <div class="fm-user-kpi"><small>APPLICATIONS</small><strong>${applications}</strong><span>Loan applications</span></div>
        </div>
        <div class="fm-user-table">
          <table><thead><tr><th>CUSTOMER ID</th><th>CUSTOMER CODE</th><th>CUSTOMER</th><th>MOBILE</th><th>BUSINESS</th><th>TYPE</th><th>KYC</th><th>STATUS</th></tr></thead>
          <tbody>${records.length?records.map(u=>`
            <tr>
              <td><b>#${esc(u.customer_id??u.id)}</b></td>
              <td><span class="fm-code">${esc(u.customer_code)}</span></td>
              <td><strong>${esc(u.customer_name??u.name)}</strong></td>
              <td>${esc(u.mobile)}</td>
              <td>${esc(u.business_name)}</td>
              <td>${esc(u.customer_type||'Individual')}</td>
              <td><span class="fm-status ${String(u.kyc_status).toLowerCase()==='verified'?'ok':'pending'}">${esc(u.kyc_status||'Not available')}</span></td>
              <td><span class="fm-pill">${esc(u.status||'active')}</span></td>
            </tr>`).join(''):'<tr><td colspan="8">No registered users found.</td></tr>'}</tbody>
          </table>
        </div>`;
    }catch(err){
      console.error('Registration & Users render failed',err);
      host.innerHTML='<div class="fm-empty"><strong>Registration & Users unavailable</strong><p>Unable to load registration data. The reporting service could not be read.</p><small>'+esc(err?.message||err)+'</small></div>';
    }
  }
  renderUsers();
})();