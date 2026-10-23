(function(){
const el=document.getElementById('reports'); if(!el)return;
const style=document.createElement('style');style.textContent="\n#reports{font-family:Inter,Arial,sans-serif;color:#17223a;background:#fff;min-height:100vh;padding:18px 20px 30px}\n.an-shell{max-width:100%;margin:0 auto}\n.an-head{display:flex;justify-content:space-between;align-items:center;gap:18px;margin:0 0 14px}\n.an-head h1{margin:0;font-size:22px;color:#132b52;letter-spacing:-.3px}\n.an-head p{margin:4px 0 0;font-size:10px;color:#718096}\n.an-actions{display:flex;align-items:center;gap:8px}\n.an-source{font-size:8px;font-weight:800;color:#087d4d;background:#eaf8f0;border-radius:14px;padding:7px 10px}\n.an-refresh{border:1px solid #d9e1eb;background:#fff;border-radius:7px;padding:7px 11px;font-size:9px;font-weight:800;color:#23446e;cursor:pointer}\n.an-cards{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:9px;margin-bottom:14px}\n.an-card{height:92px;border-radius:9px;color:#fff;display:flex;align-items:center;padding:10px 11px;gap:9px;box-shadow:0 2px 6px rgba(30,45,75,.12)}\n.an-card.purple{background:linear-gradient(135deg,#713be7,#5424d5)}.an-card.blue{background:linear-gradient(135deg,#1768ed,#0b53dc)}.an-card.red{background:linear-gradient(135deg,#f20d2d,#e60827)}.an-card.green{background:linear-gradient(135deg,#0ca35a,#078d4b)}.an-card.orange{background:linear-gradient(135deg,#ff8700,#ed7000)}\n.an-card-icon{width:28px;height:28px;border-radius:7px;background:rgba(255,255,255,.14);display:grid;place-items:center;font-size:15px;flex:0 0 auto}\n.an-card-body{min-width:0}.an-card-label{font-size:9px;font-weight:800;line-height:1.2;white-space:normal}.an-card-value{font-size:20px;font-weight:900;line-height:1;margin-top:8px}.an-card-info{float:right;font-size:9px;opacity:.9}\n.an-funnel{border:1px solid #e0e5ec;border-radius:9px;overflow:hidden;background:#fff}\n.an-funnel-title{padding:15px 14px 10px;font-size:13px;font-weight:800;color:#172b4d}\n.an-table{width:100%;border-collapse:collapse;table-layout:fixed}\n.an-table th{background:#fafbfd;color:#59677b;font-size:7px;font-weight:900;text-align:left;padding:9px 12px;border-top:1px solid #edf0f4}\n.an-table td{font-size:9px;color:#27364d;padding:11px 12px;border-top:1px solid #edf0f4;vertical-align:middle}\n.an-table td:first-child{font-weight:800;color:#1f2e46}\n.an-table .num{text-align:left}\n.an-table .repeat{color:#6940c8;font-weight:800}.an-table .completed{color:#168b50;font-weight:800}.an-table .pending{color:#bd6c32;font-weight:800}.an-table .dropped{color:#e02c3d;font-weight:800}.an-table .drop{color:#e02c3d;font-weight:800}\n.an-note{font-size:8px;color:#697789;padding:8px 12px 13px}\n.an-empty{padding:30px;background:#fff;border:1px solid #e0e5ec;border-radius:9px;color:#617087;font-size:11px}\n@media(max-width:1100px){.an-cards{grid-template-columns:repeat(4,1fr)}}\n@media(max-width:750px){#reports{padding:12px}.an-head{align-items:flex-start}.an-cards{grid-template-columns:repeat(2,1fr)}.an-funnel{overflow:auto}.an-table{min-width:760px}}\n";style.textContent += `
/* Analytics fit-to-page refinement */
#reports{box-sizing:border-box;width:100%;max-width:100%;min-width:0;padding:20px 22px 28px!important;overflow-x:hidden!important;background:#f4f7fb!important;color:#14243a!important;font-size:13px!important}
#reports *{box-sizing:border-box}
#reports .an-shell{width:100%;max-width:100%;min-width:0}
#reports .an-head{margin-bottom:18px;align-items:center;flex-wrap:wrap}
#reports .an-head h1{font-size:clamp(25px,2vw,32px);font-weight:800;line-height:1.2;color:#14243a}
#reports .an-head p{font-size:12px;line-height:1.5;margin-top:6px}
#reports .an-source{font-size:10px;padding:8px 11px}
#reports .an-refresh{font-size:11px;padding:9px 13px;border-radius:8px}
#reports .an-cards{grid-template-columns:repeat(7,minmax(0,1fr));gap:10px;margin-bottom:18px}
#reports .an-card{height:auto;min-height:104px;min-width:0;padding:14px 12px;border-radius:12px;gap:10px;box-shadow:0 4px 12px rgba(20,36,58,.08)}
#reports .an-card-icon{width:32px;height:32px;font-size:16px;flex:0 0 32px}
#reports .an-card-label{font-size:11px;line-height:1.35;font-weight:750;overflow-wrap:anywhere}
#reports .an-card-info{font-size:10px}
#reports .an-card-value{font-size:clamp(18px,1.5vw,24px);line-height:1.2;margin-top:10px;overflow-wrap:anywhere}
#reports .an-funnel{border:1px solid #dfe7f0;border-radius:12px;box-shadow:0 3px 12px rgba(20,36,58,.04)}
#reports .an-funnel-title{padding:16px 18px 13px;font-size:16px;color:#14243a}
#reports .an-table{table-layout:fixed;width:100%;min-width:0}
#reports .an-table th{font-size:10px;line-height:1.3;padding:12px 10px;overflow-wrap:anywhere}
#reports .an-table td{font-size:12px;line-height:1.4;padding:14px 10px;overflow-wrap:anywhere}
#reports .an-table th:first-child,#reports .an-table td:first-child{width:19%}
#reports .an-note{font-size:10px;padding:12px 16px 14px}
#reports .an-empty{font-size:13px;padding:24px}
@media(max-width:1250px){#reports{padding:16px!important}#reports .an-cards{grid-template-columns:repeat(4,minmax(0,1fr))}#reports .an-card{min-height:96px}}
@media(max-width:850px){#reports .an-cards{grid-template-columns:repeat(2,minmax(0,1fr))}#reports .an-table{min-width:700px}#reports .an-funnel{overflow-x:auto}#reports .an-head{align-items:flex-start}}
@media(max-width:520px){#reports{padding:12px!important}#reports .an-cards{grid-template-columns:1fr 1fr;gap:8px}#reports .an-card{padding:11px 9px;min-height:88px;gap:7px}#reports .an-card-icon{width:27px;height:27px;flex-basis:27px}#reports .an-card-label{font-size:10px}#reports .an-card-value{font-size:18px}#reports .an-head h1{font-size:24px}}
`;document.head.appendChild(style);
const esc=v=>String(v??'—').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
let d=null;
const money=v=>'₹'+Number(v||0).toLocaleString('en-IN',{maximumFractionDigits:0});
const num=v=>Number(v||0).toLocaleString('en-IN');
const pct=(a,b)=>Number(b)?((Number(a||0)/Number(b))*100).toFixed(1)+'%':'0%';

function card(label,value,cls,icon){
  return '<div class="an-card '+cls+'"><div class="an-card-icon">'+icon+'</div><div class="an-card-body"><div class="an-card-label">'+label+' <span class="an-card-info">ⓘ</span></div><div class="an-card-value">'+num(value)+'</div></div></div>';
}
function fallbackFunnel(){
  const a=Number(d.applications||0),u=Number(d.unique_users||0),r=Number(d.repeat_users||0),p=Number(d.pending||0),drop=Number(d.rejected||0);
  const completed=Math.max(a-p-drop,0),dis=Number(d.disbursed_count||0);
  return [
    {name:'Approval Stage',applications:a,unique_users:u,repeat_users:r,completed,pending:p,dropped:drop},
    {name:'E-Sign',applications:completed,unique_users:Math.min(u,completed),repeat_users:Math.min(r,completed),completed:completed,pending:0,dropped:0},
    {name:'E-Mandate',applications:dis,unique_users:Math.min(u,dis),repeat_users:Math.min(r,dis),completed:dis,pending:0,dropped:0},
    {name:'Disbursement',applications:dis,unique_users:Math.min(u,dis),repeat_users:Math.min(r,dis),completed:dis,pending:0,dropped:0}
  ];
}
function journeyFunnel(){
  const jf=d.analytics_funnel||{};
  if(!Object.keys(jf).length)return fallbackFunnel();
  const a=Number(d.applications||0),u=Number(d.unique_users||0),r=Number(d.repeat_users||0);
  const approval=jf.approval||{applications:a,unique_users:u,repeat_users:r,completed:Math.max(a-Number(d.pending||0)-Number(d.rejected||0),0),pending:d.pending||0,dropped:d.rejected||0};
  return [
    ['Approval Stage',approval],
    ['E-Sign',jf.e_sign],
    ['E-Mandate',jf.e_mandate],
    ['Disbursement',jf.disbursement]
  ].map(([name,x])=>x?{name,...x}:null).filter(Boolean);
}
function render(){
  const a=d.analytics_cards||{};
  const cards=[
    ['Unique Applicants',a.unique_applicants??d.unique_users,'purple','♙'],
    ['Total Applications',a.total_applications??d.applications,'blue','▤'],
    ['Rejected Loans',a.rejected_loans??d.rejected,'red','♙'],
    ['Repaid (LMS)',a.repaid_lms??d.repaid_loans,'green','✓'],
    ['Overdue (LMS)',a.overdue_lms??d.overdue_loans,'red','♙'],
    ['Upcoming (LMS)',a.upcoming_lms??0,'blue','◷'],
    ['Due Today (LMS)',a.due_today_lms??0,'orange','⌁']
  ];
  const rows=journeyFunnel();
  el.innerHTML='<div class="an-shell"><div class="an-head"><div><h1>Analytics</h1><p>Loan application funnel and LMS portfolio movement.</p></div><div class="an-actions"><span class="an-source">'+(d.source==='demo'?'Demo test data':'Live database')+'</span><button class="an-refresh" id="anRefresh">↻ Refresh</button></div></div><div class="an-cards">'+cards.map(x=>card(x[0],x[1],x[2],x[3])).join('')+'</div><section class="an-funnel"><div class="an-funnel-title">Loan Application Funnel <span style="font-size:9px;color:#8a95a5">ⓘ</span></div><table class="an-table"><thead><tr><th>STAGE</th><th>APPLICATIONS ⓘ</th><th>UNIQUE<br>USERS ⓘ</th><th>REPEAT<br>USERS ⓘ</th><th>COMPLETED ⓘ</th><th>PENDING ⓘ</th><th>DROPPED ⓘ</th><th>DROP % ⓘ</th></tr></thead><tbody>'+rows.map(x=>{
    const dropPct=Number(x.applications)?(Number(x.dropped||0)/Number(x.applications)*100).toFixed(1)+'%':'0%';
    return '<tr><td>'+esc(x.name)+'</td><td>'+num(x.applications)+'</td><td>'+num(x.unique_users)+'</td><td class="repeat">'+num(x.repeat_users)+'</td><td class="completed">'+num(x.completed)+'</td><td class="pending">'+num(x.pending)+'</td><td class="dropped">'+num(x.dropped)+'</td><td class="drop">'+dropPct+'</td></tr>';
  }).join('')+'</tbody></table><div class="an-note">Repaid '+num(a.repaid_lms??d.repaid_loans)+' · Overdue '+num(a.overdue_lms??d.overdue_loans)+' · Upcoming '+num(a.upcoming_lms??0)+' · Due today '+num(a.due_today_lms??0)+'</div></section></div>';
  document.getElementById('anRefresh').onclick=load;
}
async function load(){
  el.innerHTML='<div class="an-empty">Loading analytics…</div>';
  try{d=await DirectCreditData.reporting();render();}
  catch(e){try{d=DirectCreditData.demoReporting();d.source='demo';render();}catch(err){el.innerHTML='<div class="an-empty">Analytics data unavailable.</div>';}}
}
load();
})();