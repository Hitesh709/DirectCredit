(function(){
  const dash=document.getElementById('dashboard');
  if(!dash)return;
  const stages=[
    ['Approval Stage','25,919','16,665','5,743','9,161','313','16,445','63.4%'],
    ['E-Sign','9,161','5,653','2,158','8,859','302','0','0%'],
    ['E-Mandate','8,859','5,389','2,135','8,767','92','0','0%'],
    ['Disbursement','8,722','5,311','2,125','8,705','17','0','0%']
  ];
  dash.innerHTML=`<div class="dash-page-head"><span>1. DASHBOARD OVERVIEW</span></div><h2 class="dash-title">Dashboard</h2><div class="dash-cards">
  <div class="dash-card purple"><div class="dash-label">♙ <span>Unique<br>Applicants</span></div><b>16,665</b></div>
  <div class="dash-card blue"><div class="dash-label">▣ <span>Total<br>Applications</span></div><b>25,919</b></div>
  <div class="dash-card red"><div class="dash-label">♙ <span>Rejected Loans</span></div><b>16,445</b></div>
  <div class="dash-card green"><div class="dash-label">✓ <span>Repaid (LMS)</span></div><b>4,892</b></div>
  <div class="dash-card red"><div class="dash-label">♙ <span>Overdue (LMS)</span></div><b>1,619</b></div>
  <div class="dash-card blue"><div class="dash-label">◷ <span>Upcoming (LMS)</span></div><b>2,081</b></div>
  <div class="dash-card orange"><div class="dash-label">↗ <span>Due Today<br>(LMS)</span></div><b>113</b></div></div>
  <div class="dash-funnel panel"><h2>Loan Application Funnel <small>ⓘ</small></h2><div class="dash-table-wrap"><table class="dash-table"><thead><tr><th>STAGE</th><th>APPLICATIONS ⓘ</th><th>UNIQUE<br>USERS ⓘ</th><th>REPEAT<br>USERS ⓘ</th><th>COMPLETED ⓘ</th><th>PENDING ⓘ</th><th>DROPPED ⓘ</th><th>DROP<br>% ⓘ</th></tr></thead><tbody>${stages.map(r=>`<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td><td class="repeat">${r[3]}</td><td class="completed">${r[4]}</td><td class="pending">${r[5]}</td><td class="dropped">${r[6]}${r[0]==='Approval Stage'?'<small>63.4%</small>':''}</td><td>${r[7]}</td></tr>`).join('')}</tbody></table></div><div class="dash-note">Repaid 4,892 · Overdue 1,619 · Upcoming 2,081 · Due today 113</div></div>`;
})();
