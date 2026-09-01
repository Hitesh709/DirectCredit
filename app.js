const pages=[...document.querySelectorAll('.page')];
const navs=[...document.querySelectorAll('.nav')];
const titles={
  dashboard:'Dashboard',
  reports:'Reports',
  loanRequest:'Loan Request & Eligibility',
  pipeline:'Loans',
  profile:'Customers',
  bank:'Bank Analysis',
  risk:'Risk & Score',
  trend:'Loan Trend & Summary',
  slab:'Loan Slab Performance Matrix',
  disbursementMatrix:'Disbursement',
  accounting:'Accounting',
  repayment:'Repayment',
  calendar:'Due Calendar',
  settlement:'Loan Settlement / Closure',
  collection:'Collection & Agent Performance',
  alerts:'Alerts',
  documents:'Documents',
  settings:'Settings',
  support:'Support',
  logout:'Logout'
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
