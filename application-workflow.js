(()=>{
  const picker=document.getElementById('applicationPicker');
  const list=document.getElementById('applicationPickerList');
  const search=document.getElementById('applicationSearch');
  const count=document.getElementById('pickerCount');
  const tabs=[...document.querySelectorAll('.summary-tab')];
  let rows=[];
  let activeStatus='all';
  const money=v=>Number(v||0).toLocaleString('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0});
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=v=>String(v??'').trim().toLowerCase().replace(/[\s-]+/g,'_');

  function statusOf(r){
    const s=norm(r.status||r.loan_status||r.stage||r.current_stage);
    if(['rejected','reject','declined','decline'].includes(s))return 'rejected';
    if(['pending','submitted','assessment','manual_review','under_review','review'].includes(s))return 'pending';
    if(['approved','approve','sanctioned','sanction','active','servicing','disbursed','repaid','overdue'].includes(s))return 'approved';
    return Number(r.sanctioned_amount||0)>0?'approved':'pending';
  }
  function sanctionedOf(r){return Number(r.sanctioned_amount||0)>0 || ['sanctioned','disbursed','active','servicing','repaid','overdue'].includes(norm(r.status||r.stage));}
  function approvalEligible(r){return statusOf(r)!=='rejected';}

  function buildRows(reporting){
    const loanRows=Array.isArray(reporting?.loan_records)?reporting.loan_records:[];
    if(loanRows.length)return loanRows.map(r=>({...r,customer_id:r.customer_id,customer_name:r.customer_name||'Customer',business_name:r.business_name||'',application_id:r.loan_id??r.id,status:r.status||r.stage,source:r.source||'live'}));
    const customerRows=Array.isArray(reporting?.customer_records)?reporting.customer_records:[];
    return customerRows.map(c=>({...c,customer_id:c.customer_id??c.id,customer_name:c.customer_name||c.name,source:c.source||'live'}));
  }

  function mergeDemo(list){
    const demo=window.DirectCreditData?.demoCustomers||[];
    const mapped=demo.map(c=>({customer_id:c.id,customer_name:c.name,business_name:c.business_name,application_id:c.loan?.id,requested_amount:c.loan?.requested_amount,eligible_amount:c.loan?.eligible_amount,sanctioned_amount:c.loan?.sanctioned_amount,disbursed_amount:c.loan?.disbursed_amount,outstanding_amount:c.loan?.outstanding_amount,status:c.loan?.status,stage:c.loan?.current_stage,source:'demo',customer_code:c.customer_code}));
    return list.length?[...list,...mapped]:mapped;
  }

  function num(...values){
    for(const v of values){const n=Number(v);if(Number.isFinite(n))return n;}
    return 0;
  }

  function setSummary(reporting={}){
    const base=rows;
    const total=num(reporting.applications,reporting.total_applications,reporting.total,base.length);
    const rowApproved=base.filter(r=>statusOf(r)==='approved').length;
    const rowPending=base.filter(r=>statusOf(r)==='pending').length;
    const rowRejected=base.filter(r=>statusOf(r)==='rejected').length;
    const approved=num(reporting.approved,reporting.approved_applications,reporting.approvals,rowApproved);
    const pending=num(reporting.pending,reporting.pending_applications,rowPending);
    const rejected=num(reporting.rejected,reporting.rejected_applications,rowRejected);
    const approvalRaw=reporting.approval_rate ?? reporting.approval_percent ?? reporting.approval_percentage;
    const approval=approvalRaw!==undefined && approvalRaw!==null ? Number(approvalRaw) : (total?approved/total*100:0);
    const rowSanctioned=base.reduce((s,r)=>s+Number(r.sanctioned_amount||0),0);
    const sanctioned=num(reporting?.amounts?.sanctioned,reporting.sanctioned_amount,reporting.sanctioned_amount_total,rowSanctioned);
    document.getElementById('summaryTotal').textContent=total.toLocaleString('en-IN');
    document.getElementById('summaryApproved').textContent=approved.toLocaleString('en-IN');
    document.getElementById('summaryPending').textContent=pending.toLocaleString('en-IN');
    document.getElementById('summaryRejected').textContent=rejected.toLocaleString('en-IN');
    document.getElementById('summaryApproval').textContent=`${Number.isFinite(approval)?approval.toFixed(1):'0.0'}%`;
    document.getElementById('summarySanctioned').textContent=money(sanctioned);
  }

  function matches(r,term){if(!term)return true;const hay=[r.customer_name,r.customer_code,r.business_name,r.application_id,r.mobile,r.email,r.status,r.stage].join(' ').toLowerCase();return hay.includes(term.toLowerCase());}
  function filtered(){const term=search?.value.trim()||'';return rows.filter(r=>{let ok=true;if(activeStatus==='approved')ok=statusOf(r)==='approved';else if(activeStatus==='pending')ok=statusOf(r)==='pending';else if(activeStatus==='rejected')ok=statusOf(r)==='rejected';else if(activeStatus==='approval')ok=approvalEligible(r);else if(activeStatus==='sanctioned')ok=sanctionedOf(r);return ok&&matches(r,term);});}

  function renderList(){
    const data=filtered();
    count.textContent=`${data.length} customer${data.length===1?'':'s'}`;
    if(!data.length){list.innerHTML='<div class="picker-empty">No applications match this selection.</div>';return;}
    list.innerHTML=data.map((r,i)=>{const stage=r.status||r.stage||'Pending';const amount=r.sanctioned_amount||r.requested_amount||r.eligible_amount||0;return `<button class="picker-row" type="button" data-row-index="${i}"><span class="picker-main"><span class="picker-name">${esc(r.customer_name||'Customer')}</span><span class="picker-sub">${esc(r.business_name||'')} ${r.application_id?'• Application #'+esc(r.application_id):''} ${r.customer_code?'• '+esc(r.customer_code):''}</span></span><span class="picker-meta"><span class="picker-stage">${esc(stage)}</span><span class="picker-amount">${money(amount)}</span></span></button>`;}).join('');
    [...list.querySelectorAll('.picker-row')].forEach(btn=>btn.addEventListener('click',()=>selectCustomer(data[Number(btn.dataset.rowIndex)])));
  }

  function openPicker(status){
    activeStatus=status||'all';tabs.forEach(t=>t.classList.toggle('active',t.dataset.status===activeStatus));
    const labels={all:'All Applications',approved:'Approved Applications',pending:'Pending Applications',rejected:'Rejected Applications',approval:'Applications Included in Approval',sanctioned:'Sanctioned Applications'};
    document.getElementById('pickerTitle').textContent=labels[activeStatus]||'Select Customer';
    document.getElementById('pickerSubtitle').textContent='Select a customer to open the full Customer, Contact, Banking, KYC, Risk and Eligibility workspace.';
    search.value='';renderList();picker.classList.add('open');picker.setAttribute('aria-hidden','false');setTimeout(()=>search.focus(),20);
  }
  function closePicker(){picker.classList.remove('open');picker.setAttribute('aria-hidden','true');}
  function selectCustomer(r){
    const source=r.source==='demo'?'demo':'live', value=`${source}:${r.customer_id}`;closePicker();let tries=0;
    const apply=()=>{const select=document.getElementById('applicationSelector');if(select){const option=[...select.options].find(o=>o.value===value);if(option){select.value=value;select.dispatchEvent(new Event('change',{bubbles:true}));return;}}if(tries++<30)setTimeout(apply,100);else{const url=new URL(location.href);url.searchParams.set('customer_id',r.customer_id);url.searchParams.set('source',source);location.href=url.toString();}};apply();
  }

  async function loadSummary(){
    try{
      let reporting=null;
      if(window.DirectCreditData?.reporting)reporting=await window.DirectCreditData.reporting({force:true});
      rows=mergeDemo(buildRows(reporting));
      setSummary(reporting||{});
      renderList();
    }catch(e){
      rows=mergeDemo([]);
      setSummary({applications:rows.length});
      renderList();
      console.error('Applications summary load failed:',e);
    }
  }

  tabs.forEach(t=>t.addEventListener('click',()=>openPicker(t.dataset.status)));
  document.querySelectorAll('[data-picker-close]').forEach(x=>x.addEventListener('click',closePicker));
  search.addEventListener('input',renderList);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&picker.classList.contains('open'))closePicker()});
  document.getElementById('refreshBtn')?.addEventListener('click',()=>loadSummary());
  setSummary({applications:0,approved:0,pending:0,rejected:0,approval_rate:0,sanctioned_amount:0});
  loadSummary();
})();