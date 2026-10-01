(async()=>{
const el=document.getElementById('pipeline');if(!el)return;
const num=v=>Number(v||0).toLocaleString('en-IN');
const pct=(a,b)=>Number(b)?((Number(a||0)/Number(b))*100).toFixed(1)+'%':'0.0%';
const get=async()=>{if(!window.DirectCreditData){await new Promise((ok,no)=>{const s=document.createElement('script');s.src='admin-data.js?v=20261001.15';s.onload=ok;s.onerror=no;document.head.appendChild(s)});}return DirectCreditData.reporting()};
try{
const d=await get(), a=Number(d.applications||0),u=Number(d.unique_users||0),r=Number(d.repeat_users||0),dis=Number(d.disbursed_count||0);
const jf=d.analytics_funnel||{}, ap=jf.approval||{completed:Math.max(a-Number(d.pending||0)-Number(d.rejected||0),0),pending:d.pending||0,dropped:d.rejected||0};
const rows=[
['Applications',a,'100%','100%',''],
['Unique Users',u,pct(u,a),pct(u,a),'blue'],
['Repeat Users',r,pct(r,u),pct(r,a),'green'],
['Completed',ap.completed||0,a?((ap.completed/a)*100).toFixed(1)+'%':'0%',pct(ap.completed,a),'green'],
['Pending',ap.pending||0,pct(ap.pending,a),pct(ap.pending,a),'orange'],
['Dropped / Rejected',ap.dropped||0,pct(ap.dropped,a),pct(ap.dropped,a),'red'],
['Disbursement',dis,pct(dis,ap.completed||a),pct(dis,a),'orange']
];
const cards=[
['Total Applications',a,'purple','▤','Lifetime'],['Unique Applicants',u,'blue','♙','Lifetime'],
['Repeat Applicants',r,'green','♙',pct(r,a)+' of total'],['Rejected Loans',d.rejected,'red','×',pct(d.rejected,a)+' of total'],
['Repaid (LMS)',d.repaid_loans,'green','✓',pct(d.repaid_loans,a)+' of total'],['Overdue (LMS)',d.overdue_loans,'red','⚠',pct(d.overdue_loans,a)+' of total'],
['Upcoming (LMS)',d.analytics_cards?.upcoming_lms||0,'blue','◷',pct(d.analytics_cards?.upcoming_lms||0,a)+' of total']
];
const visual=[['Applications',a,pct(a,a)],['Unique Users',u,pct(u,a)],['Repeat Users',r,pct(r,a)],['Disbursement',dis,pct(dis,a)]];
el.innerHTML='<div class="lp-head"><div><h2><span>2</span> LOAN PIPELINE &amp; FUNNEL</h2><p>Application to Disbursement Pipeline</p></div><div class="lp-actions"><button onclick="location.reload()">⟳ &nbsp;Refresh</button><button type="button">☰ &nbsp;Filter</button></div></div>'+
'<div class="lp-kpis">'+cards.map(c=>'<div class="lp-kpi '+c[2]+'"><div class="lp-icon">'+c[3]+'</div><div><b>'+c[0]+'</b><strong>'+num(c[1])+'</strong><small>'+c[4]+'</small></div></div>').join('')+'</div>'+
'<div class="lp-panel"><h3>Loan Application Funnel</h3><div class="lp-funnel-grid"><div><div class="funnel-visual">'+visual.map((x,i)=>'<div class="funnel-step f'+(i+1)+'">'+num(x[1])+'</div>').join('')+visual.map((x,i)=>'<div class="funnel-label l'+(i+1)+'"><b>'+x[0]+'</b><span>'+x[2]+'</span></div>').join('')+'</div><div class="lp-legend"><span>● Applications</span><span>● Unique Users</span><span>● Repeat Users</span><span>● Disbursement</span></div></div>'+
'<div class="lp-table-wrap"><table class="lp-table"><thead><tr><th>STAGE</th><th>COUNT</th><th>% OF PREVIOUS STAGE</th><th>% OF TOTAL</th></tr></thead><tbody>'+rows.map(x=>'<tr><td class="'+x[4]+'">'+x[0]+'</td><td>'+num(x[1])+'</td><td>'+x[2]+'</td><td>'+x[3]+'</td></tr>').join('')+'</tbody></table></div></div></div>'+
'<div class="lp-bottom"><div class="lp-bottom-item green"><div class="lp-bottom-icon">✓</div><div><b>Repaid (LMS)</b><strong>'+num(d.repaid_loans)+'</strong><small>'+pct(d.repaid_loans,a)+' of total</small></div></div><div class="lp-bottom-item red"><div class="lp-bottom-icon">⚠</div><div><b>Overdue (LMS)</b><strong>'+num(d.overdue_loans)+'</strong><small>'+pct(d.overdue_loans,a)+' of total</small></div></div><div class="lp-bottom-item blue"><div class="lp-bottom-icon">◷</div><div><b>Upcoming (LMS)</b><strong>'+num(d.analytics_cards?.upcoming_lms||0)+'</strong><small>'+pct(d.analytics_cards?.upcoming_lms||0,a)+' of total</small></div></div><div class="lp-bottom-item orange"><div class="lp-bottom-icon">▣</div><div><b>Due Today</b><strong>'+num(d.analytics_cards?.due_today_lms||0)+'</strong><small>Loans due today</small></div></div></div>';
}catch(e){el.innerHTML='<div class="lp-panel"><h3>Reporting data unavailable</h3><p>Unable to load the DirectCredit reporting service.</p></div>';console.error(e)}
})();