(function(){
  const el=document.getElementById('reports');
  if(!el)return;
  const tabs=[
    ['Registration & Users','Registered users, MoM matrix, and onboarding...','users'],
    ['Loan Pipeline','Approval → E-Sign → E-Mandate → Disbursement','pipeline'],
    ['Disbursement Matrix','Disbursement counts by date/time → new vs...','disbursement'],
    ['Loan Slab Performance','Active, overdue & repaid by loan amount slab','slab'],
    ['Repayment Matrix','Due-date collection matrix — cash received → DPD...','repayment'],
    ['Due Calendar','Month-wise due-date collection calendar and...','calendar']
  ];
  const registered=[
    ['Total Registered','86,816','blue'],['Last Active This Month','21,729','green'],['Awaiting Approval','316','orange'],['Rejected / Dropped','16,877','red'],['Onboarding Completed','25,983','teal'],['Profile Incomplete','60,791','purple']
  ];
  const mom=[
    ['Registered Users','86,816','50,328','13,005','-74.2%'],
    ['Onboarding Completed','25,983','15,342','3,189','-79.2%'],
    ['Profile Incomplete','60,791','34,806','9,812','-71.8%'],
    ['Blocked / Deactivated','434','180','4','-97.8%']
  ];
  const funnel=[
    ['Aadhaar Verification','86,816','63,228','23,303','285','0.3%','72.8%'],
    ['PAN Verification','63,228','55,862','7,358','8','0%','88.4%'],
    ['Selfie & Liveness','55,862','50,525','5,330','7','0%','90.4%'],
    ['Personal Details','50,525','47,730','2,791','4','0%','94.5%'],
    ['CIBIL Score Check','47,730','35,013','12,711','6','0%','73.4%'],
    ['Bank Account Details','35,013','25,596','9,298','119','0.3%','73.1%']
  ];
  el.innerHTML=`
    <div class="fr-head">
      <div><h2>Funnel & Matrix Reports</h2><p>Registered users, MoM matrix, and onboarding stage conversion</p><small>Updated 08/May/2026, 12:25:57 PM</small></div>
      <div class="fr-admin"><div class="fr-admin-avatar">●</div><div><b>Service Matrimony</b><span>Super Admin</span></div><button class="fr-refresh">⟳ &nbsp;Refresh</button></div>
    </div>
    <div class="fr-tabs">${tabs.map((t,i)=>`<button class="fr-tab ${i===0?'selected':''}" data-report-tab="${t[2]}"><span class="fr-tab-icon">${['♙','▤','$','▦','%','□'][i]}</span><div><b>${t[0]}</b><small>${t[1]}</small></div></button>`).join('')}</div>
    <div class="fr-filter"><div class="fr-filter-label">▣ <b>Registration date & time</b><small>All registration dates</small></div><input placeholder="dd/mm/yyyy, --:-- --"><span>to</span><input placeholder="dd/mm/yyyy, --:-- --"><button>Apply</button></div>
    <h3 class="fr-section-title">Registered Users <span>ⓘ</span></h3>
    <div class="fr-kpis">${registered.map(k=>`<div class="fr-kpi ${k[2]}"><span class="fr-kpi-icon">${k[2]==='orange'?'◷':k[2]==='red'?'♙':k[2]==='green'?'↗':k[2]==='teal'?'✓':k[2]==='purple'?'✎':'♙'}</span><div><b>${k[0]}</b><strong>${k[1]}</strong><span>ⓘ</span></div></div>`).join('')}</div>
    <div class="fr-bottom">
      <div class="fr-panel"><h3>Month-over-month breakdown</h3><table><thead><tr><th>METRIC</th><th>TOTAL</th><th>PREVIOUS MONTH</th><th>THIS MONTH</th><th>MOM GROWTH %</th></tr></thead><tbody>${mom.map(r=>`<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td><td>${r[3]}</td><td class="fr-negative">${r[4]}</td></tr>`).join('')}</tbody></table></div>
      <div class="fr-panel"><h3>Onboarding Funnel <span>ⓘ</span></h3><table><thead><tr><th>STAGE</th><th>REGISTERED</th><th>COMPLETED</th><th>PENDING</th><th>DROPPED</th><th>DROP %</th><th>CONV %</th></tr></thead><tbody>${funnel.map(r=>`<tr><td>${r[0]}</td><td>${r[1]}</td><td class="fr-positive">${r[2]}</td><td class="fr-pending">${r[3]}</td><td class="fr-drop">${r[4]}</td><td>${r[5]}</td><td>${r[6]}</td></tr>`).join('')}</tbody></table></div>
    </div>`;
})();
