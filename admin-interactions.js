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
    const m=document.createElement('div');m.id='dcDrillModal';m.hidden=true;m.innerHTML=`<div class="dc-drill-card" role="dialog" aria-modal="true" aria-labelledby="dcDrillTitle"><div class="dc-drill-head"><h2 id="dcDrillTitle">Details</h2><button class="dc-drill-close" type="button">Close</button></div><div class="dc-drill-body" id="dcDrillBody"></div></div>`;
    document.body.appendChild(m);m.querySelector('.dc-drill-close').onclick=()=>m.hidden=true;m.onclick=e=>{if(e.target===m)m.hidden=true};
  }
  function reporting(){return window.DirectCreditData?.reporting?window.DirectCreditData.reporting():fetch((localStorage.getItem('directcredit_api_url')||'/api')+'/admin/reporting').then(r=>r.json())}
  function loans(){return window.DirectCreditData?.loans?window.DirectCreditData.loans():Promise.resolve([])}
  function detail(key,label,row){
    ensure(); Promise.all([reporting(),loans()]).then(([d,ls])=>{
      const rows=Array.isArray(ls)?ls:[];
      const customers=(window.DirectCreditData?.customer)?null:null;
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
      document.getElementById('dcDrillModal').hidden=false;
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
    const el=e.target.closest('[data-drill-key]');if(el&&!e.target.closest('button,input,select,a')){detail(el.dataset.drillKey,el.dataset.drillLabel,el);return}
    const row=e.target.closest('table tbody tr');if(row&&!e.target.closest('button,input,select,a')&&row.children.length&&!row.querySelector('td[colspan]')){detail('row',row.closest('.fr-panel,.dc-panel,.panel,.accounting-panel,.settlement-panel,.collection-page,.fm-view')?.querySelector('h2,h3')?.innerText||'Record',row);return}
  });
  window.DCExport={exportPage,detail}; ensure(); addBar();
})();