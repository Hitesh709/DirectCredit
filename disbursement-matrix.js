(function(){
  const el=document.getElementById('disbursementMatrix');
  if(!el)return;
  const rows=[
    ['Disbursed (Count)',['0','75','248','846','3,126','1,001'],'5,296','883','60.7%',['0','2','149','295','2,195','795'],'3,436','573','8,732'],
    ['Disbursed (₹ Lakhs)',['0.00','3.00','9.92','18.99','50.58','15.76'],'98.25','16.38','54.6%',['0.00','0.14','6.56','10.16','45.85','18.14'],'80.85','13.48','179.10'],
    ['Applications (Count)',['15','184','760','3,606','13,008','3,894'],'21,467','3,578','60.9%',['0','2','188','375','2,725','1,162'],'4,452','742','25,919'],
    ['Repaid (₹ Lakhs)',['0.00','2.30','9.18','19.01','44.36','1.83'],'76.68','12.78','57.0%',['0.00','0.20','7.28','11.30','38.93','0.70'],'58.41','9.74','135.08'],
    ['Overdue Amount (₹ Lakhs)',['0.00','2.04','4.87','7.38','16.17','0.12'],'30.58','5.10','48.8%',['0.00','0.00','1.84','2.76','9.70','0.01'],'14.31','2.39','44.89']
  ];
  const months=['MAR-26','APR-26','MAY-26','JUN-26','JUL-26','AUG-26'];
  el.innerHTML=`
    <div class="dm-head"><div><h2><span>3</span> DISBURSEMENT MATRIX</h2><p>Month-wise comparison — Disbursement</p></div><button class="dm-refresh">⟳ &nbsp; Refresh</button></div>
    <div class="dm-kpis">
      <div class="dm-kpi dark"><i>♙</i><div><b>Total Disbursed</b><strong>8,732</strong><small>Lifetime</small></div></div>
      <div class="dm-kpi blue"><i>✓</i><div><b>New Disbursed</b><strong>5,296</strong><small>60.7%</small></div></div>
      <div class="dm-kpi purple"><i>♧</i><div><b>Repeat Disbursed</b><strong>3,436</strong><small>39.3%</small></div></div>
      <div class="dm-kpi green"><i>₹</i><div><b>Total Amount</b><strong>₹1.8 Cr</strong><small>Lifetime</small></div></div>
    </div>
    <div class="dm-table-wrap"><table class="dm-table"><thead>
      <tr><th rowspan="2">METRIC</th><th colspan="9" class="new">NEW USERS</th><th colspan="9" class="repeat">REPEAT USERS</th><th rowspan="2">GRAND<br>TOTAL</th></tr>
      <tr>${months.map(m=>`<th>${m}</th>`).join('')}<th>TOTAL</th><th>AVG. (₹L)</th><th>% OF TOTAL</th>${months.map(m=>`<th>${m}</th>`).join('')}<th>TOTAL</th><th>AVG. (₹L)</th><th>% OF TOTAL</th></tr>
    </thead><tbody>${rows.map((r,idx)=>`<tr><td>${r[0]}</td>${r[1].map(v=>`<td class="newv">${v}</td>`).join('')}<td class="bold">${r[2]}</td><td class="bold">${r[3]}</td><td class="bold">${r[4]}</td>${r[5].map(v=>`<td class="repeatv">${v}</td>`).join('')}<td class="bold">${r[6]}</td><td class="bold">${r[7]}</td><td class="bold">${idx===2?'':r[8]}</td><td class="grand">${r[9]}</td></tr>`).join('')}</tbody></table></div>
    <div class="dm-filters"><label>▣ <span>Month</span><select><option>August</option></select></label><label><span>Year</span><select><option>2026</option></select></label><label><span>User Type</span><select><option>All</option></select></label><label><span>Loan Amount Slab</span><select><option>All</option></select></label><label><span>Location</span><select><option>All Location</option></select></label><button>⇩ &nbsp; Export Report</button></div>
    <div class="dm-notes"><div><b>● &nbsp; Notes</b><ul><li><strong>New Users:</strong> First-time borrowers in the system.</li><li><strong>Repeat Users:</strong> Existing borrowers who took multiple loans.</li></ul></div><ul><li><strong>Average (₹ L):</strong> Average disbursement amount in Lakhs.</li><li><strong>% of Total:</strong> Share of each segment in total disbursement.</li></ul></div>`;
})();
