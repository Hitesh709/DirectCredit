(function(){
 if(window.__dcDeepDetailLoaded)return; window.__dcDeepDetailLoaded=true;
 const base=()=>((localStorage.getItem('directcredit_api_url')||window.DIRECTCREDIT_API_URL||'/api').replace(/\/$/,''));
 const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const money=v=>'₹'+Number(v||0).toLocaleString('en-IN',{maximumFractionDigits:2});
 const auth=()=>{const t=localStorage.getItem('directcredit_admin_token')||window.DIRECTCREDIT_ADMIN_TOKEN;return t?{Authorization:'Bearer '+t}:{}};
 async function profile(id){if(window.DirectCreditData?.customer)return window.DirectCreditData.customer(id);const r=await fetch(base()+'/admin/reports/customer/'+encodeURIComponent(id)+'/profile',{headers:auth()});if(!r.ok)throw Error(r.status);return r.json()}
 function ensure(){
  if(document.getElementById('dcDeepModal'))return;
  const s=document.createElement('style');s.textContent='.dcdeep{position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:100000;display:flex;align-items:center;justify-content:center;padding:16px}.dcdeep[hidden]{display:none}.dcdeep-card{background:#fff;width:min(1200px,100%);max-height:94vh;overflow:auto;border-radius:14px;box-shadow:0 24px 70px rgba(0,0,0,.25)}.dcdeep-head{position:sticky;top:0;background:#fff;z-index:3;display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid #e5e7eb}.dcdeep-head h2{margin:0;font-size:18px}.dcdeep-actions{display:flex;gap:6px}.dcdeep-btn{border:1px solid #d9e0ea;background:#fff;border-radius:8px;padding:7px 10px;cursor:pointer}.dcdeep-body{padding:18px 20px}.dcdeep-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.dcdeep-card{border:1px solid #e5e7eb;border-radius:10px;padding:11px}.dcdeep-card small{display:block;color:#64748b;font-size:10px;text-transform:uppercase}.dcdeep-card b{display:block;margin-top:4px}.dcdeep-tabs{display:flex;gap:5px;overflow:auto;border-bottom:1px solid #e5e7eb;margin:0 0 14px}.dcdeep-tab{border:0;background:#fff;padding:9px 12px;white-space:nowrap;cursor:pointer;font-weight:600}.dcdeep-tab.active{color:#2563eb;border-bottom:2px solid #2563eb}.dcdeep-table{width:100%;border-collapse:collapse;font-size:12px}.dcdeep-table th,.dcdeep-table td{padding:8px;border-bottom:1px solid #edf0f4;text-align:left;vertical-align:top}.dcdeep-table th{background:#f8fafc}.dcdeep-empty{padding:18px;border:1px dashed #cbd5e1;border-radius:10px;color:#64748b;text-align:center}@media(max-width:760px){.dcdeep-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.dcdeep-body{padding:12px}.dcdeep-table{min-width:780px}}';document.head.appendChild(s);
  const m=document.createElement('div');m.id='dcDeepModal';m.className='dcdeep';m.hidden=true;m.innerHTML='<div class="dcdeep-card"><div class="dcdeep-head"><h2 id="dcDeepTitle">Customer 360</h2><div class="dcdeep-actions"><button class="dcdeep-btn" id="dcDeepCsv">Export CSV</button><button class="dcdeep-btn" id="dcDeepPrint">Print / PDF</button><button class="dcdeep-btn" id="dcDeepClose">Close</button></div></div><div class="dcdeep-body" id="dcDeepBody"></div></div>';document.body.appendChild(m);
  m.onclick=e=>{if(e.target===m)m.hidden=true};document.getElementById('dcDeepClose').onclick=()=>m.hidden=true;document.getElementById('dcDeepPrint').onclick=()=>window.print();document.getElementById('dcDeepCsv').onclick=()=>{const d=window.__dcDeepExport;if(!d)return;const rows=d.rows?[['Customer ID','Customer','Business','Mobile','Loan ID','Requested','Disbursed','Outstanding','Status','Stage'],...d.rows]:[['Field','Value'],...Object.entries(d.customer||{}).map(x=>x)];const csv=rows.map(r=>r.map(v=>'"'+String(v??'').replace(/"/g,'""')+'"').join(',')).join('\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='directcredit-detail.csv';document.body.appendChild(a);a.click();a.remove();};
 }
 function card(k,v){return '<div class="dcdeep-card"><small>'+esc(k)+'</small><b>'+esc(v==null||v===''?'Not available':v)+'</b></div>'}
 function table(head,rows){if(!rows.length)return '<div class="dcdeep-empty">No records available.</div>';return '<div style="overflow:auto"><table class="dcdeep-table"><thead><tr>'+head.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(x=>'<td>'+esc(x)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>'}
 async function openCustomer(id,title){
  if(!id)return;ensure();const body=document.getElementById('dcDeepBody');document.getElementById('dcDeepTitle').textContent=title||('Customer '+id+' — Customer 360');body.innerHTML='<div class="dcdeep-empty">Loading Customer 360…</div>';document.getElementById('dcDeepModal').hidden=false;
  try{
   const p=await profile(id),c=p.customer||{},m=p.metrics||{},b=p.bank_analysis||{},k=p.kyc_employment||{},r=p.risk_score||{},ls=p.loans||[],rs=p.repayments||[],docs=p.documents||[],tx=p.bank_transactions||[],j=p.journey||[];
   const views={
    overview:'<div class="dcdeep-grid">'+card('Customer ID',c.id)+card('Customer Code',c.customer_code)+card('Name',c.name)+card('Mobile',c.mobile)+card('Business',c.business_name)+card('Business Type',c.business_type)+card('City',c.current_city)+card('KYC',c.kyc_status)+card('Total Loans',m.total_loans)+card('Total Loan Amount',money(m.total_loan_amount))+card('Outstanding',money(m.outstanding_amount))+card('Amount Paid',money(m.amount_paid))+card('Overdue',money(m.overdue_amount))+card('CIBIL',r.credit_score)+card('DirectCredit Score',r.total_score)+card('Decision',r.decision)+'</div>',
    loans:'<h3>Loan history / portfolio</h3>'+table(['Loan ID','Product','Requested','Eligible','Sanctioned','Disbursed','Outstanding','EMI','Tenure','Rate','Status','Stage'],ls.map(x=>[x.id,x.product,money(x.requested_amount),money(x.eligible_amount),money(x.sanctioned_amount),money(x.disbursed_amount),money(x.outstanding_amount),money(x.monthly_emi),x.tenure_months?x.tenure_months+' months':'—',x.interest_rate==null?'—':x.interest_rate+'%',x.status,x.current_stage])),
    repayments:'<h3>Repayment schedule / performance</h3>'+table(['ID','Loan','Installment','Due Date','Due','Paid','Unpaid','Status','DPD'],rs.map(x=>[x.id,x.loan_id,x.installment,x.due_date,money(x.due_amount),money(x.paid_amount),money(Math.max((x.due_amount||0)-(x.paid_amount||0),0)),x.status,x.dpd??'—'])),
    bank:'<div class="dcdeep-grid">'+card('Transactions',b.total_transactions)+card('Credits',b.credit_transactions)+card('Debits',b.debit_transactions)+card('Last Balance',money(b.last_balance))+card('Average EOD',money(b.average_eod_balance))+card('Avg Monthly Credit',money(b.average_monthly_credit))+card('Avg Monthly Debit',money(b.average_monthly_debit))+card('Negative Balance Events',b.negative_balance_count)+'</div><h3>Recent bank transactions</h3>'+table(['Date','Direction','Amount','Category','Description','Reference','Balance'],tx.slice(0,100).map(x=>[x.transaction_date,x.direction,money(x.amount),x.category,x.description,x.reference,money(x.balance)])),
    kyc:'<div class="dcdeep-grid">'+card('KYC Status',k.kyc_status)+card('Occupation',k.employment_type)+card('Monthly Income',money(k.income))+card('Business Vintage',k.years_in_business==null?'—':k.years_in_business+' years')+card('Work Experience',k.work_experience_years==null?'—':k.work_experience_years+' years')+card('Residence Ownership',k.residence_ownership)+card('Ownership Proof',k.ownership_proof_status)+card('Ownership Proof Name',k.ownership_proof_name)+'</div><h3>Documents</h3>'+table(['Document','Loan','File','Verification','Created'],docs.map(x=>[x.document_type,x.loan_id,x.file_name,x.verification_status,x.created_at])),
    risk:'<div class="dcdeep-grid">'+card('Score',r.total_score==null?'Not assessed':r.total_score)+card('Max Score',r.max_score||125)+card('Decision',r.decision)+card('Approval',r.approval_percent==null?'—':r.approval_percent+'%')+card('Risk Tier',r.risk_tier)+card('CIBIL',r.credit_score)+card('FOIR',r.foir==null?'—':r.foir+'%')+card('Existing EMI',money(r.existing_emi))+'</div><h3>Score-factor breakdown</h3>'+table(['Factor','Points'],Object.entries(r.factor_scores||{}))+ '<h3>Assessment reasons</h3><ul>'+(r.reasons||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul><h3>Hard reject reasons</h3><ul>'+(r.hard_rejects||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>',
    docs:table(['Document','Loan','File','Verification','Created'],docs.map(x=>[x.document_type,x.loan_id,x.file_name,x.verification_status,x.created_at])),
    journey:table(['Step','Status','Loan','Updated','Details'],j.map(x=>[x.step_label||x.step_key,x.status,x.loan_id,x.updated_at,JSON.stringify(x.details||{})]))
   };
   const keys=Object.keys(views), tabs=keys.map(k=>'<button class="dcdeep-tab" data-v="'+k+'">'+k.replace(/_/g,' ')+'</button>').join('');
   body.innerHTML='<div class="dcdeep-tabs">'+tabs+'</div><div id="dcDeepView"></div><p style="font-size:12px;color:#64748b">Data comes from the protected Customer 360 profile aggregation. Missing fields are shown as Not available.</p>';
   const render=k=>{document.getElementById('dcDeepView').innerHTML=views[k];document.querySelectorAll('.dcdeep-tab').forEach(x=>x.classList.toggle('active',x.dataset.v===k))};
   document.querySelectorAll('.dcdeep-tab').forEach(x=>x.onclick=()=>render(x.dataset.v));render('overview');
   window.__dcDeepExport={customer:c,metrics:m,bank:b,risk:r,loans:ls,repayments:rs,documents:docs,bank_transactions:tx,journey:j};
  }catch(e){body.innerHTML='<div class="dcdeep-empty">Customer detail could not be loaded. Verify the authorized admin token and API connection.</div>'}
 }

 async function openAggregate(key,title){
  ensure();
  const body=document.getElementById('dcDeepBody');document.getElementById('dcDeepTitle').textContent=(title||key)+' — Detailed Breakdown';body.innerHTML='<div class="dcdeep-empty">Loading detailed breakdown…</div>';document.getElementById('dcDeepModal').hidden=false;
  try{
   const rows0=window.DirectCreditData?.loans?await window.DirectCreditData.loans():await fetch(base()+'/admin/reports/loan-pipeline',{headers:auth()}).then(x=>x.json());
   const rows=Array.isArray(rows0)?rows0:(rows0.rows||[]);
   let filtered=rows;
   if(key==='total-disbursed')filtered=rows.filter(x=>Number(x.disbursed_amount||x.amount)>0);
   else if(key==='outstanding')filtered=rows.filter(x=>Number(x.outstanding_amount)>0);
   else if(key==='overdue')filtered=rows.filter(x=>String(x.status).toLowerCase()==='overdue');
   else if(key==='active')filtered=rows.filter(x=>String(x.status).toLowerCase()==='active');
   else if(key==='repaid'||key==='paid')filtered=rows.filter(x=>String(x.status).toLowerCase()==='repaid');
   else if(key==='pending')filtered=rows.filter(x=>['pending','assessment','review'].includes(String(x.status).toLowerCase()));
   else if(key==='closed')filtered=rows.filter(x=>['closed','settled','written_off','repaid'].includes(String(x.status).toLowerCase()));
   const money2=money;
   const data=filtered.map(x=>[x.customer_id,x.customer_name||'Not available',x.business_name||'Not available',x.mobile||'Not available','LN'+String(x.loan_id??x.id).padStart(8,'0'),money2(x.requested_amount),money2(x.disbursed_amount??x.amount),money2(x.outstanding_amount),x.status,x.stage||x.current_stage||'—']);
   body.innerHTML='<div class="dcdeep-grid">'+card('Records',data.length)+card('Function',title||key)+card('Source','Live loan pipeline')+'</div><p style="font-size:12px;color:#64748b">Customer-wise breakdown. Click any row to open the complete Customer 360 record.</p>'+table(['Customer ID','Customer','Business','Mobile','Loan ID','Requested','Disbursed','Outstanding','Status','Stage'],data);
   window.__dcDeepExport={function:key,rows:data};
   body.querySelectorAll('tbody tr').forEach((tr,i)=>tr.onclick=()=>openCustomer(Number(data[i][0]),data[i][1]+' — '+data[i][4]));
  }catch(e){body.innerHTML='<div class="dcdeep-empty">Detailed breakdown is unavailable. Verify the authorized admin token and API connection.</div>'}
 }
 document.addEventListener('click',e=>{
  const row=e.target.closest('table tbody tr');
  const cardEl=e.target.closest('[data-drill-key]');
  if(!row&&!cardEl)return;
  if(e.target.closest('button,input,select,a'))return;
  if(cardEl && !row){const key=cardEl.dataset.drillKey;if(key){e.preventDefault();e.stopImmediatePropagation();openAggregate(key,cardEl.dataset.drillLabel||cardEl.innerText.split('\\n')[0]);return;}}
  const text=(row||cardEl).innerText||'';
  const cm=(text.match(/(?:CUST|customer(?:\s+id)?)[\s:#-]*(\d+)/i)||[])[1];
  if(cm){e.preventDefault();e.stopImmediatePropagation();openCustomer(Number(cm),'Customer '+cm+' — Detail');return}
  const lm=(text.match(/(?:LN|loan(?:\s+id)?)[\s:#-]*(\d+)/i)||[])[1];
  if(lm){const loanId=Number(lm);const customer=(text.match(/(?:CUST|customer(?:\s+id)?)[\s:#-]*(\d+)/i)||[])[1];if(customer){e.preventDefault();e.stopImmediatePropagation();openCustomer(Number(customer),'Loan '+loanId+' — Customer '+customer);}}
 },true);
 document.addEventListener('DOMContentLoaded',ensure);
})();