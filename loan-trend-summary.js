const months=['Nov ’25','Dec ’25','Jan ’26','Feb ’26','Mar ’26','Apr ’26'];
const disbursed=[42.10,45.32,48.67,52.14,51.38,58.72];
const loans=[1842,1962,2072,2218,2188,2461];
const svg=document.getElementById('trendChart');
function renderChart(){
  const W=760,H=290,p={l:48,r:42,t:18,b:42},cw=W-p.l-p.r,ch=H-p.t-p.b;
  const maxA=70,maxL=3000;
  let s='';
  for(let i=0;i<=7;i++){const y=p.t+ch*i/7;const v=Math.round(maxA*(1-i/7));s+=`<line x1="${p.l}" y1="${y}" x2="${W-p.r}" y2="${y}" stroke="#e4e9f0" stroke-dasharray="3 3"/><text x="${p.l-8}" y="${y+3}" text-anchor="end" font-size="9" fill="#68758a">${v}</text>`}
  months.forEach((m,i)=>{const x=p.l+cw*i/(months.length-1);s+=`<line x1="${x}" y1="${p.t}" x2="${x}" y2="${p.t+ch}" stroke="#edf0f5"/><text x="${x}" y="${H-18}" text-anchor="middle" font-size="9" fill="#53627a">${m}</text>`});
  const pts=disbursed.map((v,i)=>[p.l+cw*i/(months.length-1),p.t+ch*(1-v/maxA)]);
  const lp=loans.map((v,i)=>[p.l+cw*i/(months.length-1),p.t+ch*(1-v/maxL)]);
  s+=`<path d="M ${pts.map(x=>x.join(' ')).join(' L ')}" fill="none" stroke="#155bd5" stroke-width="3"/>`;
  pts.forEach((q,i)=>{s+=`<circle cx="${q[0]}" cy="${q[1]}" r="4" fill="#155bd5"/><text x="${q[0]}" y="${q[1]-10}" text-anchor="middle" font-size="9" font-weight="700" fill="#155bd5">${disbursed[i].toFixed(2)}</text>`});
  s+=`<path d="M ${lp.map(x=>x.join(' ')).join(' L ')}" fill="none" stroke="#24975f" stroke-width="2"/>`;
  lp.forEach((q,i)=>{s+=`<circle cx="${q[0]}" cy="${q[1]}" r="3" fill="#24975f"/><text x="${q[0]}" y="${q[1]+15}" text-anchor="middle" font-size="8" fill="#24975f">${loans[i].toLocaleString()}</text>`});
  s+=`<text x="10" y="${p.t+ch/2}" transform="rotate(-90 10 ${p.t+ch/2})" font-size="9" fill="#65738a">₹ Cr</text><text x="${W-8}" y="${p.t+ch/2}" transform="rotate(90 ${W-8} ${p.t+ch/2})" font-size="9" fill="#65738a">No. of Loans</text>`;
  svg.innerHTML=s;
}
renderChart();
document.getElementById('trendPeriod').addEventListener('change',e=>{if(e.target.value==='12 Months'){alert('12-month trend data will be populated from the live reporting dataset.');e.target.value='6 Months';}});
document.getElementById('filterBtn').addEventListener('click',()=>{alert('Filters: Branch, Product, User Type, Loan Amount Slab and Loan Status.');});
document.getElementById('exportBtn').addEventListener('click',()=>{
  const rows=[['Product','Total Loans','Disbursed Amount (Cr)','Outstanding (Cr)','Overdue (Cr)','NPA (Cr)'],['Business Term Loan',1125,28.56,17.82,.28,.08],['Working Capital Loan',842,18.21,11.43,.19,.05],['Loan Against Property',256,7.85,5.12,.08,.02],['Equipment Loan',138,2.75,1.68,.02,.01],['Overdraft Facility',100,1.35,.83,.01,.01]];
  const csv=rows.map(r=>r.join(',')).join('\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='DirectCredit_Loan_Trend_Summary.csv';a.click();URL.revokeObjectURL(a.href);
});