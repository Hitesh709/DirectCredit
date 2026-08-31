(function(){
  const el=document.getElementById('pipeline');
  if(!el)return;
  const cards=[
    ['Total Applications','25,919','Lifetime','purple'],
    ['Unique Applicants','16,665','Lifetime','blue'],
    ['Repeat Applicants','5,743','35.5% of total','green'],
    ['Rejected Loans','16,445','63.4% of total','red'],
    ['Repaid (LMS)','4,892','18.9% of total','green'],
    ['Overdue (LMS)','1,619','6.2% of total','red'],
    ['Upcoming (LMS)','2,081','8.0% of total','blue']
  ];
  const stages=[
    ['Applications','25,919','100%','100%','purple'],
    ['Unique Users','16,665','64.3%','64.3%','blue'],
    ['Repeat Users','5,743','34.5%','22.2%','green'],
    ['Completed','9,161','159.4%','35.3%','green'],
    ['Pending','313','3.4%','1.2%','orange'],
    ['Dropped / Rejected','16,445','63.4%','63.4%','red'],
    ['Disbursement','8,705','95.0%','33.6%','orange']
  ];
  const bottom=[['Repaid (LMS)','4,892','18.9% of total','green'],['Overdue (LMS)','1,619','6.2% of total','red'],['Upcoming (LMS)','2,081','8.0% of total','blue'],['Due Today','113','Loans due today','orange']];
  el.innerHTML=`
    <div class="lp-head"><div><h2><span>2</span> LOAN PIPELINE &amp; FUNNEL</h2><p>Application to Disbursement Pipeline</p></div><div class="lp-actions"><button>⟳ &nbsp;Refresh</button><button>☰ &nbsp;Filter</button></div></div>
    <div class="lp-kpis">${cards.map(c=>`<div class="lp-kpi ${c[3]}"><div class="lp-icon">${c[3]==='red'?'×':c[3]==='green'?'✓':c[3]==='orange'?'▣':c[3]==='purple'?'▤':'♙'}</div><div><b>${c[0]}</b><strong>${c[1]}</strong><small>${c[2]}</small></div></div>`).join('')}</div>
    <div class="lp-panel"><h3>Loan Application Funnel</h3><div class="lp-funnel-grid"><div class="funnel-visual"><div class="funnel-step f1"><b>25,919</b></div><div class="funnel-label l1"><b>Applications</b><span>100%</span></div><div class="funnel-step f2"><b>16,665</b></div><div class="funnel-label l2"><b>Unique Users</b><span>64.3%</span></div><div class="funnel-step f3"><b>5,743</b></div><div class="funnel-label l3"><b>Repeat Users</b><span>35.5%</span></div><div class="funnel-step f4"><b>8,705</b></div><div class="funnel-label l4"><b>Disbursement</b><span>33.6%</span></div><div class="lp-legend"><span>● Applications</span><span>● Unique Users</span><span>● Repeat Users</span><span>● Disbursement</span></div></div><div class="lp-table-wrap"><table class="lp-table"><thead><tr><th>STAGE</th><th>COUNT</th><th>% OF PREVIOUS STAGE</th><th>% OF TOTAL</th></tr></thead><tbody>${stages.map(r=>`<tr><td class="${r[4]}">${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td><td>${r[3]}</td></tr>`).join('')}</tbody></table></div></div></div>
    <div class="lp-bottom">${bottom.map(b=>`<div class="lp-bottom-item ${b[3]}"><span class="lp-bottom-icon">${b[3]==='green'?'✓':b[3]==='red'?'⚠':b[3]==='blue'?'◷':'▣'}</span><div><b>${b[0]}</b><strong>${b[1]}</strong><small>${b[2]}</small></div></div>`).join('')}</div>`;
})();
