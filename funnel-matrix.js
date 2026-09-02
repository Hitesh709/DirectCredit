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
  const base=(localStorage.getItem('directcredit_api_url')||window.DIRECTCREDIT_API_URL||'/api').replace(/\/$/,'');
  const val=v=>v===null||v===undefined||v===''?'—':v;
  const esc=v=>String(val(v)).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  Promise.all([
    fetch(base+'/customers',{headers:{Accept:'application/json'}}).then(r=>{if(!r.ok)throw Error('Customers API '+r.status);return r.json()}),
    fetch(base+'/admin/reporting',{headers:{Accept:'application/json'}}).then(r=>{if(!r.ok)throw Error('Reporting API '+r.status);return r.json()})
  ]).then(([users,report])=>{
    const rows=Array.isArray(users)?users:[];
    const verified=rows.filter(x=>String(x.kyc_status||'').toLowerCase()==='verified').length;
    const active=rows.filter(x=>String(x.status||'active').toLowerCase()==='active').length;
    const withMobile=rows.filter(x=>String(x.mobile||'').trim()).length;
    host.innerHTML=`<div class="fm-users-head"><div><h2>Registration & Users</h2><p>Live customer registration master. No demo users are displayed.</p></div></div>
      <div class="fm-user-kpis">
        <div class="fm-user-kpi"><small>TOTAL REGISTERED USERS</small><strong>${rows.length}</strong></div>
        <div class="fm-user-kpi"><small>ACTIVE USERS</small><strong>${active}</strong></div>
        <div class="fm-user-kpi"><small>KYC VERIFIED</small><strong>${verified}</strong></div>
        <div class="fm-user-kpi"><small>USERS WITH MOBILE</small><strong>${withMobile}</strong></div>
      </div>
      <div class="fm-user-table"><table><thead><tr><th>CUSTOMER ID</th><th>CUSTOMER CODE</th><th>NAME</th><th>MOBILE</th><th>BUSINESS</th><th>TYPE</th><th>KYC STATUS</th><th>STATUS</th></tr></thead><tbody>${rows.length?rows.map(u=>`<tr><td>${esc(u.id)}</td><td>${esc(u.customer_code)}</td><td>${esc(u.name)}</td><td>${esc(u.mobile)}</td><td>${esc(u.business_name)}</td><td>${esc(u.customer_type)}</td><td>${esc(u.kyc_status)}</td><td><span class="fm-pill">${esc(u.status||'active')}</span></td></tr>`).join(''):'<tr><td colspan="8">No registered users found in the live database.</td></tr>'}</tbody></table></div>`;
  }).catch(err=>{
    console.warn('Registration & Users live data unavailable:',err.message);
    host.innerHTML='<div class="fm-empty"><strong>Registration & Users unavailable</strong><p>Connect the DirectCredit API. No dummy or fallback users are displayed.</p></div>';
  });
})();