(function(){
  const dash=document.getElementById('dashboard'); if(!dash)return;
  const kpis=[
    ['Total Users','Registrations completed in app','25,981','blue','♙'],
    ['Active Loans','Currently active loans','3,840','purple','▣'],
    ['Overdue Loans','Loans currently overdue','1,610','red','⚠'],
    ['Active Disbursed Amount','Disbursed & overdue loans','₹78,88,150','green','$'],
    ['Active Net Outflow','Cash sent on active & overdue loans','₹38,53,751','orange','↘'],
    ['Total Disbursed Amount','Includes disbursed, overdue & repaid','₹1,79,10,050','teal','↗'],
    ['Total Outflow','Total loan cash outflow','₹1,41,53,275','amber','↘'],
    ['Pending Repayment','Amount pending for repayment','₹1,06,43,556','pink','▤']
  ];
  const trend=[729,742,685,812,765,861,735,864,315,42,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
  const points=trend.map((v,i)=>`${18+i*18},${180-(v/900)*150}`).join(' ');
  const dots=trend.map((v,i)=>`<circle cx="${18+i*18}" cy="${180-(v/900)*150}" r="2.6"/>`).join('');
  dash.innerHTML=`
  <div class="dc-head"><div><b>Dashboard:</b><span>Loan Pipeline - We required All loan Application stage As Described Above</span></div><button class="dc-refresh" onclick="location.reload()">⟳ &nbsp;Refresh</button></div>
  <div class="dc-title">Dashboard</div>
  <div class="dc-kpis">${kpis.map(k=>`<div class="dc-kpi ${k[3]}"><div class="dc-kpi-icon">${k[4]}</div><div class="dc-kpi-info"><div class="dc-kpi-name">${k[0]} <span>ⓘ</span></div><div class="dc-kpi-sub">${k[1]}</div><strong>${k[2]}</strong></div></div>`).join('')}</div>
  <div class="dc-main-grid"><div class="dc-left">
    <div class="dc-panel dc-trend"><div class="dc-panel-head"><h3>Loan Trend</h3><div class="dc-filters"><select><option>August</option></select><select><option>2026</option></select><select><option>Applications</option></select></div></div>
      <div class="dc-chart"><div class="dc-ylabels"><span>900</span><span>800</span><span>600</span><span>400</span><span>200</span><span>0</span></div><svg viewBox="0 0 570 205" preserveAspectRatio="none"><g class="gridlines"><line x1="18" y1="30" x2="558" y2="30"/><line x1="18" y1="60" x2="558" y2="60"/><line x1="18" y1="90" x2="558" y2="90"/><line x1="18" y1="120" x2="558" y2="120"/><line x1="18" y1="150" x2="558" y2="150"/><line x1="18" y1="180" x2="558" y2="180"/></g><polyline points="${points}" fill="none" class="trend-line"/>${dots.replace(/<circle/g,'<circle class="trend-dot"')}</svg><div class="dc-xlabels">${Array.from({length:31},(_,i)=>`<span>${i+1}</span>`).join('')}</div></div>
    </div>
    <div class="dc-panel dc-recent"><div class="dc-panel-head"><h3>Recent Loans</h3><button class="dc-view">View All ›</button></div><table><thead><tr><th>Loan ID</th><th>Customer Name</th><th>Loan Amount</th><th>Status</th><th>Disbursed On</th><th>Due Date</th><th></th></tr></thead><tbody><tr><td>LN123456</td><td>Amit Sharma</td><td>₹25,000</td><td><span class="dc-status">Active</span></td><td>07/08/2026</td><td>07/09/2026</td><td>•••</td></tr></tbody></table></div>
  </div><div class="dc-right">
    <div class="dc-panel dc-summary"><div class="dc-panel-head"><h3>Summary</h3><input type="date" value="2026-08-08"/></div><div class="dc-row"><span>New Applications</span><b>223</b></div><div class="dc-row"><span>Pending Approvals</span><b>165</b></div><div class="dc-row"><span>Due Repayments</span><b>0</b></div><div class="dc-row danger"><span>Overdue Loans</span><b>1610</b></div><div class="dc-row success"><span>Completed Loans</span><b>72</b></div></div>
    <div class="dc-panel dc-notify"><div class="dc-panel-head"><h3>Recent Notifications</h3><span class="dc-new">50 new</span><span class="dc-trash">♧</span></div><div class="dc-notice"><div class="dc-avatar">♙</div><div><b>User Activity</b><small>New user registered - Rajesh Kumar</small></div><time>2m ago</time><span>›</span></div></div>
  </div></div>`;
  if(!location.hash && typeof showPage==='function') showPage('dashboard');
})();
