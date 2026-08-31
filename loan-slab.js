(function(){
  const el=document.getElementById('slab'); if(!el)return;
  const rows=[
    ['₹5,000','203','₹1,42,100','13%','372','₹2,60,400','24%','979','₹6,85,300','63%','10,87,800'],
    ['₹7,500','413','₹4,33,650','22%','408','₹2,84,400','22%','1,044','₹10,96,200','56%','19,58,250'],
    ['₹10,000','632','₹12,64,000','56%','74','₹1,48,000','7%','423','₹8,46,000','37%','22,58,000'],
    ['₹12,500','333','₹8,32,500','22%','264','₹6,60,000','17%','912','₹22,80,000','60%','37,72,500'],
    ['₹15,000','325','₹13,00,000','20%','346','₹13,84,000','21%','979','₹39,16,000','59%','66,00,000'],
    ['TOTAL','2,230','₹47,14,100','20%','1,610','₹31,74,200','18%','4,892','₹100,22,200','56%','₹1,79,10,050']
  ];
  el.innerHTML=`
    <div class="slab-head"><div><h2><span>4</span> LOAN SLAB PERFORMANCE MATRIX</h2><p>Loan Slab Performance Matrix — Active, Overdue &amp; Repaid</p></div><button class="slab-refresh">⟳ &nbsp; Refresh</button></div>
    <div class="slab-kpis">
      <div class="slab-kpi dark"><div><b>TOTAL LOANS (ALL SLABS)</b><strong>8,732</strong><small>₹179.10L</small></div><i>ⓘ</i></div>
      <div class="slab-kpi blue"><div><b>ACTIVE LOANS</b><strong>2,230</strong><small>₹47.14L (26%)</small></div><i>ⓘ</i></div>
      <div class="slab-kpi red"><div><b>OVERDUE LOANS</b><strong>1,610</strong><small>₹31.74L (18%)</small></div><i>ⓘ</i></div>
      <div class="slab-kpi green"><div><b>REPAID LOANS</b><strong>4,892</strong><small>₹100.22L (56%)</small></div><i>ⓘ</i></div>
    </div>
    <div class="slab-table-wrap"><table class="slab-table"><thead><tr><th rowspan="2">LOAN AMOUNT</th><th colspan="3" class="active">ACTIVE LOANS</th><th colspan="3" class="overdue">OVERDUE</th><th colspan="3" class="repaid">REPAID</th><th rowspan="2">GRAND TOTAL</th></tr><tr><th>COUNT</th><th>AMOUNT</th><th>%</th><th>COUNT</th><th>AMOUNT</th><th>%</th><th>COUNT</th><th>AMOUNT</th><th>%</th></tr></thead><tbody>${rows.map((r,i)=>`<tr class="${i===rows.length-1?'total':''}"><td>${r[0]}</td><td class="activev">${r[1]}</td><td class="activev">${r[2]}</td><td class="activev">${r[3]}</td><td class="overduev">${r[4]}</td><td class="overduev">${r[5]}</td><td class="overduev">${r[6]}</td><td class="repaidv">${r[7]}</td><td class="repaidv">${r[8]}</td><td class="repaidv">${r[9]}</td><td class="grand">${r[10]}</td></tr>`).join('')}</tbody></table></div>`;
})();
