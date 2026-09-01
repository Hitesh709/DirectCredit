const pages=[...document.querySelectorAll('.page')];
const navs=[...document.querySelectorAll('.nav')];
const titles={
  dashboard:'Dashboard',reports:'Funnel & Matrix Reports',pipeline:'Loan Pipeline',profile:'Customer Profile',
  kyc:'KYC & Employment Summary',contact:'Number & Contact Details',bank:'Bank Statement Analysis',risk:'Risk & Score Breakdown',
  trend:'Loan Trend & Summary',loanRequest:'Loan Request & Eligibility',slab:'Loan Slab Performance Matrix',
  disbursementMatrix:'Disbursement Matrix',accounting:'Loan Accounting & Repayment',repayment:'Repayment Matrix',
  calendar:'Due Calendar',settlement:'Loan Settlement / Closure',collection:'Collection & Agent Performance'
};
function showPage(id){
  pages.forEach(p=>p.classList.toggle('activePage',p.id===id));
  navs.forEach(n=>n.classList.toggle('active',n.dataset.page===id));
  const title=document.getElementById('pageTitle');
  if(title) title.textContent=titles[id]||id;
  history.replaceState(null,'','#'+id);
}
navs.forEach(n=>n.addEventListener('click',()=>showPage(n.dataset.page)));
const initial=(location.hash||'#dashboard').slice(1);
showPage(titles[initial]?initial:'dashboard');
