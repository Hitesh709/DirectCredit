(function(){
  if(window.__dcInteractionsLoaded)return; window.__dcInteractionsLoaded=true;
  const fmt=v=>'₹'+Number(v||0).toLocaleString('en-IN',{maximumFractionDigits:2});
  const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function ensure(){
    if(document.getElementById('dcDrillModal'))return;
    const s=document.createElement('style');s.textContent=`
      .dc-export-bar{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin:0 0 12px}
      .dc-export-bar button,.dc-drill-btn{border:1px solid #d9e0ea;background:#fff;border-radius:8px;padding:8px 12px;cursor:pointer;font-weight:600}
      .dc-export-bar button:hover,.dc-drill-btn:hover{background:#f4f7fb}
      [data-drill-key]{cursor:pointer}.dc-clickable{transition:.15s}.dc-clickable:hover{background:#f7faff}
      #dcDrillModal{position:fixed;inset:0;background:rgba(15,23,42,.42);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px}
      #dcDrillModal[hidden]{display:none}.dc-drill-card{background:#fff;border-radius:14px;max-width:1100px;width:min(100%,1100px);max-height:88vh;overflow:auto;box-shadow:0 20px 60px rgba(0,0,0,.2)}
      .dc-drill-head{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:18px 20px;border-bottom:1px solid #e5e7eb;position:sticky;top:0;background:#fff;z-index:2}
      .dc-drill-head h2{margin:0;font-size:18px}.dc-drill-close{border:0;background:#eef2f7;border-radius:8px;padding:7px 10px;cursor:pointer}
      .dc-drill-body{padding:18px 20px}.dc-drill-meta{display:flex;gap:18px;flex-wrap:wrap;margin-bottom:14px}.dc-drill-meta b{display:block;font-size:18px}.dc-drill-meta span{font-size:11px;color:#64748b;text-transform:uppercase}
      .dc-drill-table{width:100%;border-collapse:collapse;font-size:13px}.dc-drill-table th,.dc-drill-table td{padding:9px;border-bottom:1px solid #edf0f4;text-align:left}.dc-drill-table th{background:#f8fafc;position:sticky;top:58px}
      @media(max-width:600px){#dcDrillModal{padding:8px}.dc-drill-card{max-height:94vh}.dc-drill-body{padding:12px}.dc-drill-table{min-width:720px}.dc-drill-body{overflow:auto}}
    `;document.head.appendChild(s);
    const m=document.createElement('div');m.id='dcDrillModal';m.hidden=true;m.innerHTML=`<div class="dc-drill-card" role="dialog" aria-modal="true" aria-labelledby="dcDrillTitle"><div class="dc-drill-head"><h2 id="dcDrillTitle">Details</h2><div style="display:flex;gap:6px"><button class="dc-drill-btn" type="button" data-drill-export="csv">CSV</button><button class="dc-drill-btn" type="button" data-drill-export="json">JSON</button><button class="dc-drill-close" type="button">Close</button></div></div><div class="dc-drill-body" id="dcDrillBody"></div></div>`;
    document.body.appendChild(m);m.querySelector('.dc-drill-close').onclick=()=>m.hidden=true;m.onclick=e=>{if(e.target===m)m.hidden=true};
  }
  function reporting(){return window.DirectCreditData?.reporting?window.DirectCreditData.reporting():fetch((localStorage.getItem('directcredit_api_url')||'/api')+'/admin/reporting').then(r=>r.json())}
  function loans(){return window.DirectCreditData?.loans?window.DirectCreditData.loans():Promise.resolve([])}
  function detail(key,label,row){
    ensure(); Promise.all([reporting(),loans()]).then(async ([d,ls])=>{
      const rows=Array.isArray(ls)?ls:[];
      
      let title=label||key, data=[];
      if(key==='total-disbursed'||key==='disbursed') data=rows.map(x=>({Customer:x.customer_id,'Loan ID':'LN'+String(x.id).padStart(8,'0'),'Disbursed Amount':fmt(x.disbursed_amount||x.sanctioned_amount||x.requested_amount),'Status':x.status,'Outstanding':fmt(x.outstanding_amount)}));
      else if(key==='outstanding') data=rows.filter(x=>Number(x.outstanding_amount)>0).map(x=>({Customer:x.customer_id,'Loan ID':'LN'+String(x.id).padStart(8,'0'),'Outstanding':fmt(x.outstanding_amount),'Status':x.status,'Disbursed':fmt(x.disbursed_amount)}));
      else if(key==='overdue') data=rows.filter(x=>x.status==='overdue').map(x=>({Customer:x.customer_id,'Loan ID':'LN'+String(x.id).padStart(8,'0'),'Overdue':fmt(x.outstanding_amount),'Status':x.status}));
      else if(key==='paid') data=rows.map(x=>({Customer:x.customer_id,'Loan ID':'LN'+String(x.id).padStart(8,'0'),'Paid':fmt(Math.max(Number(x.disbursed_amount||0)-Number(x.outstanding_amount||0),0)),'Status':x.status}));
      else if(key==='applications') data=rows.map(x=>({Customer:x.customer_id,'Loan ID':'LN'+String(x.id).padStart(8,'0'),'Requested':fmt(x.requested_amount),'Status':x.status}));
      else if(key==='active') data=rows.filter(x=>x.status==='active').map(x=>({Customer:x.customer_id,'Loan ID':'LN'+String(x.id).padStart(8,'0'),'Outstanding':fmt(x.outstanding_amount),'Status':x.status}));
      else if(key==='repaid') data=rows.filter(x=>x.status==='repaid').map(x=>({Customer:x.customer_id,'Loan ID':'LN'+String(x.id).padStart(8,'0'),'Disbursed':fmt(x.disbursed_amount),'Status':x.status}));
      else if(key==='pending') data=rows.filter(x=>x.status==='pending').map(x=>({Customer:x.customer_id,'Loan ID':'LN'+String(x.id).padStart(8,'0'),'Requested':fmt(x.requested_amount),'Status':x.status}));
      else if(row?.dataset?.drillPayload){try{data=JSON.parse(row.dataset.drillPayload)}catch(e){}}
      if(!data.length)data=[{Metric:label||key,Value:row?.innerText?.trim()||'No detail records'}];
      const ids=[...new Set(data.map(x=>x.Customer).filter(Boolean))]; if(ids.length&&window.DirectCreditData?.customer){const details=await Promise.all(ids.map(id=>window.DirectCreditData.customer(id).catch(()=>null))); const byId=new Map(details.filter(Boolean).map(x=>[String(x.customer?.id),x.customer])); data=data.map(x=>{const q=byId.get(String(x.Customer));return q?{Customer:x.Customer,'Customer Name':q.name||'—','Business':q.business_name||'—',Mobile:q.mobile||'—',...x}:x;});} const body=document.getElementById('dcDrillBody');document.getElementById('dcDrillTitle').textContent=title+' — Details';
      const cols=Object.keys(data[0]);body.innerHTML=`<div class="dc-drill-meta"><div><span>Records</span><b>${data.length}</b></div><div><span>Source</span><b>${window.DEMO_MODE||window.DirectCreditData?'Demo / configured data':'Portal data'}</b></div></div><div style="overflow:auto"><table class="dc-drill-table"><thead><tr>${cols.map(esc).map(x=>'<th>'+x+'</th>').join('')}</tr></thead><tbody>${data.map(r=>'<tr>'+cols.map(c=>'<td>'+esc(r[c])+'</td>').join('')+'</tr>').join('')}</tbody></table></div>`;
      window.__dcDrillData=data; document.getElementById('dcDrillModal').hidden=false;
    }).catch(()=>{ensure();document.getElementById('dcDrillTitle').textContent='Details unavailable';document.getElementById('dcDrillBody').innerHTML='<p>Unable to load detail records.</p>';document.getElementById('dcDrillModal').hidden=false});
  }
  function csvFromTable(table){
    const rows=[...table.querySelectorAll('tr')].map(tr=>[...tr.children].map(td=>'"'+String(td.innerText||'').replace(/"/g,'""')+'"').join(','));
    return rows.join('\n');
  }
  function download(name,text,type){
    const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  }
  function exportPage(kind){
    const tables=[...document.querySelectorAll('table')]; if(!tables.length){download('directcredit-data.json',JSON.stringify({exported_at:new Date().toISOString()},null,2),'application/json');return}
    if(kind==='print'){window.print();return}
    if(kind==='json'){
      const out=tables.map(t=>({headers:[...t.querySelectorAll('thead th')].map(x=>x.innerText),rows:[...t.querySelectorAll('tbody tr')].map(tr=>[...tr.children].map(td=>td.innerText))}));
      download('directcredit-export.json',JSON.stringify({exported_at:new Date().toISOString(),tables:out},null,2),'application/json');
    }else{
      download('directcredit-export.csv',tables.map(csvFromTable).join('\n\n'),'text/csv;charset=utf-8');
    }
  }
  function addBar(){
    if(document.querySelector('.dc-export-bar'))return;
    const host=document.querySelector('.main')||document.body, bar=document.createElement('div');bar.className='dc-export-bar';
    bar.innerHTML='<button type="button" data-export="csv">Export CSV</button><button type="button" data-export="json">Export JSON</button><button type="button" data-export="print">Print / PDF</button>';
    host.insertBefore(bar,host.firstChild);
  }
  function enhance(){
    document.querySelectorAll('tbody tr').forEach(row=>{if(row.children.length&&!row.querySelector('td[colspan]'))row.classList.add('dc-clickable')});
    const map=[['total disbursed','total-disbursed'],['total amount','total-disbursed'],['disbursed amount','total-disbursed'],['disbursed count','total-disbursed'],['active loans','active'],['overdue loans','overdue'],['outstanding','outstanding'],['paid amount','paid'],['amount received','paid'],['repaid loans','repaid'],['pending applications','pending'],['total applications','applications'],['applications','applications'],['unpaid','outstanding'],['total due','outstanding']];
    document.querySelectorAll('.dc-kpi,.fr-kpi,.slab-kpi,.dm-kpi,.rm-kpi,.dc-cal-kpi,.lp-kpi,.accounting-kpi,.settlement-kpi,.kpi').forEach(card=>{if(card.dataset.drillKey)return;const t=(card.innerText||'').toLowerCase();const hit=map.find(x=>t.includes(x[0]));if(hit){card.dataset.drillKey=hit[1];card.dataset.drillLabel=(card.querySelector('b,.kpi-title,.label,small')?.innerText||hit[0]).trim();card.classList.add('dc-clickable')}});
  }
  enhance(); new MutationObserver(enhance).observe(document.body,{childList:true,subtree:true});
  document.addEventListener('click',e=>{
    const exp=e.target.closest('[data-export]');if(exp){exportPage(exp.dataset.export);return}
    const de=e.target.closest('[data-drill-export]');if(de){const rows=window.__dcDrillData||[];if(!rows.length)return;const cols=Object.keys(rows[0]);if(de.dataset.drillExport==='json')download('directcredit-drilldown.json',JSON.stringify({exported_at:new Date().toISOString(),rows},null,2),'application/json');else download('directcredit-drilldown.csv',[cols.join(','),...rows.map(r=>cols.map(c=>'"'+String(r[c]??'').replace(/"/g,'""')+'"').join(','))].join('\n'),'text/csv;charset=utf-8');return}
    const el=e.target.closest('[data-drill-key]');if(el&&!e.target.closest('button,input,select,a')){detail(el.dataset.drillKey,el.dataset.drillLabel,el);return}
    const row=e.target.closest('table tbody tr');if(row&&!e.target.closest('button,input,select,a')&&row.children.length&&!row.querySelector('td[colspan]')){detail('row',row.closest('.fr-panel,.dc-panel,.panel,.accounting-panel,.settlement-panel,.collection-page,.fm-view')?.querySelector('h2,h3')?.innerText||'Record',row);return}
  });

  async function dcOpenCustomer360(customerId, title){
    if(!customerId)return;
    ensure();
    const body=document.getElementById('dcDrillBody');
    document.getElementById('dcDrillTitle').textContent=title||('Customer '+customerId+' — 360° Details');
    body.innerHTML='<div class="dc-drill-meta"><div><span>Status</span><b>Loading…</b></div></div><p>Loading Customer 360 detail…</p>';
    document.getElementById('dcDrillModal').hidden=false;
    try{
      const p=window.DirectCreditData?.customer?await window.DirectCreditData.customer(customerId):await fetch((localStorage.getItem('directcredit_api_url')||'/api')+'/admin/reports/customer/'+encodeURIComponent(customerId)+'/profile',{headers:(()=>{const t=localStorage.getItem('directcredit_admin_token')||window.DIRECTCREDIT_ADMIN_TOKEN;return t?{Authorization:'Bearer '+t}:{} })()}).then(r=>{if(!r.ok)throw Error(r.status);return r.json()});
      const c=p.customer||{},m=p.metrics||{},b=p.bank_analysis||{},k=p.kyc_employment||{},r=p.risk_score||{},loans=p.loans||[],reps=p.repayments||[],docs=p.documents||[],tx=p.bank_transactions||[],journey=p.journey||[];
      const card=(a,v)=>'<div class="dc-detail-card"><small>'+esc(a)+'</small><strong>'+esc(v==null||v===''?'Not available':v)+'</strong></div>';
      const tbl=(h,rows)=>rows.length?'<div style="overflow:auto"><table class="dc-drill-table"><thead><tr>'+h.map(esc).map(x=>'<th>'+x+'</th>').join('')+'</tr></thead><tbody>'+rows.map(x=>'<tr>'+x.map(v=>'<td>'+esc(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>':'<div class="dc-empty">No records available.</div>';
      const factors=Object.entries(r.factor_scores||{}).map(([k,v])=>[k,v]);
      body.innerHTML='<div class="dc-drill-meta">'+card('Customer ID',c.id)+card('Customer Code',c.customer_code)+card('Name',c.name)+card('Mobile',c.mobile)+card('Total Loans',m.total_loans)+card('Total Loan Amount',fmt(m.total_loan_amount))+card('Outstanding',fmt(m.outstanding_amount))+card('Overdue',fmt(m.overdue_amount))+'</div>'+
        '<div class="dc-detail-tabs"><button class="dc-detail-tab active" data-c360="overview">Overview</button><button class="dc-detail-tab" data-c360="loans">Loans</button><button class="dc-detail-tab" data-c360="repayments">Repayments</button><button class="dc-detail-tab" data-c360="bank">Bank</button><button class="dc-detail-tab" data-c360="kyc">KYC & Employment</button><button class="dc-detail-tab" data-c360="risk">Risk & Score</button><button class="dc-detail-tab" data-c360="docs">Documents</button><button class="dc-detail-tab" data-c360="journey">Journey</button></div><div id="dcC360Body"></div>';
      const views={
        overview:'<div class="dc-detail-grid">'+card('Business',c.business_name)+card('Business Type',c.business_type)+card('City',c.current_city)+card('KYC Status',c.kyc_status)+card('CIBIL',r.credit_score)+card('DirectCredit Score',r.total_score)+card('FOIR',r.foir==null?'—':r.foir+'%')+card('Existing EMI',fmt(r.existing_emi))+card('Income',fmt(c.monthly_income))+card('Residence',c.residence_ownership)+card('Primary Bank',c.primary_bank)+card('Email',c.email)+'</div>',
        loans:'<h3>Loan history / portfolio</h3>'+tbl(['Loan ID','Product','Requested','Eligible','Sanctioned','Disbursed','Outstanding','EMI','Tenure','Rate','Status','Stage'],loans.map(x=>[x.id,x.product,fmt(x.requested_amount),fmt(x.eligible_amount),fmt(x.sanctioned_amount),fmt(x.disbursed_amount),fmt(x.outstanding_amount),fmt(x.monthly_emi),x.tenure_months?x.tenure_months+' m':'—',x.interest_rate==null?'—':x.interest_rate+'%',x.status,x.current_stage])),
        repayments:'<h3>Repayment schedule / performance</h3>'+tbl(['ID','Loan','Installment','Due Date','Due','Paid','Unpaid','Status','DPD'],reps.map(x=>[x.id,x.loan_id,x.installment,x.due_date,fmt(x.due_amount),fmt(x.paid_amount),fmt(Math.max((x.due_amount||0)-(x.paid_amount||0),0)),x.status,x.dpd??'—'])),
        bank:'<div class="dc-detail-grid">'+card('Transactions',b.total_transactions)+card('Credits',b.credit_transactions)+card('Debits',b.debit_transactions)+card('Last Balance',fmt(b.last_balance))+card('Average EOD',fmt(b.average_eod_balance))+card('Avg Monthly Credit',fmt(b.average_monthly_credit))+card('Avg Monthly Debit',fmt(b.average_monthly_debit))+card('Negative Balance Events',b.negative_balance_count)+'</div>'+tbl(['Date','Direction','Amount','Category','Description','Reference','Balance'],tx.slice(0,100).map(x=>[x.transaction_date,x.direction,fmt(x.amount),x.category,x.description,x.reference,fmt(x.balance)])),
        kyc:'<div class="dc-detail-grid">'+card('KYC Status',k.kyc_status)+card('Occupation',k.employment_type)+card('Monthly Income',fmt(k.income))+card('Business Vintage',k.years_in_business==null?'—':k.years_in_business+' years')+card('Work Experience',k.work_experience_years==null?'—':k.work_experience_years+' years')+card('Residence',k.residence_ownership)+card('Ownership Proof',k.ownership_proof_status)+card('Ownership Proof Name',k.ownership_proof_name)+'</div>'+tbl(['Document','Loan','File','Verification','Created'],docs.map(x=>[x.document_type,x.loan_id,x.file_name,x.verification_status,x.created_at])),
        risk:'<div class="dc-detail-grid">'+card('Score',r.total_score==null?'Not assessed':r.total_score)+card('Max Score',r.max_score||125)+card('Decision',r.decision)+card('Approval',r.approval_percent==null?'—':r.approval_percent+'%')+card('Risk Tier',r.risk_tier)+card('CIBIL',r.credit_score)+card('FOIR',r.foir==null?'—':r.foir+'%')+card('Existing EMI',fmt(r.existing_emi))+'</div><h3>Score-factor breakdown</h3>'+tbl(['Factor','Points'],factors)+'<h3>Assessment reasons</h3><ul>'+(r.reasons||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul><h3>Hard reject reasons</h3><ul>'+(r.hard_rejects||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>',
        docs:tbl(['Document','Loan','File','Verification','Created'],docs.map(x=>[x.document_type,x.loan_id,x.file_name,x.verification_status,x.created_at])),
        journey:tbl(['Step','Status','Loan','Updated','Details'],journey.map(x=>[x.step_label||x.step_key,x.status,x.loan_id,x.updated_at,JSON.stringify(x.details||{})]))
      };
      const render=k=>{document.getElementById('dcC360Body').innerHTML=views[k]||views.overview;document.querySelectorAll('[data-c360]').forEach(b=>b.classList.toggle('active',b.dataset.c360===k))};
      document.querySelectorAll('[data-c360]').forEach(b=>b.onclick=()=>render(b.dataset.c360)); render('overview');
      window.__dcDrillData=[{customer_id:c.id,customer_code:c.customer_code,name:c.name,mobile:c.mobile,business:c.business_name,total_loans:m.total_loans,total_loan_amount:m.total_loan_amount,outstanding:m.outstanding_amount,overdue:m.overdue_amount,score:r.total_score,decision:r.decision}];
    }catch(e){body.innerHTML='<div class="dc-empty">Customer detail could not be loaded. Verify the authorized admin token and API connection.</div>'}
  }
  window.DCExport=Object.assign(window.DCExport||{},{showCustomer:dcOpenCustomer360});

  window.DCExport=Object.assign(window.DCExport||{},{exportPage,detail,showCustomer:dcOpenCustomer360}); ensure(); addBar();
})();