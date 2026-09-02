const pages=[...document.querySelectorAll('.page')];
const navs=[...document.querySelectorAll('.nav')];
const titles={
  dashboard:'Dashboard',reports:'Analytics',loanRequest:'Applications',pipeline:'Loans',
  disbursementMatrix:'Disbursement',accounting:'Accounting',repayment:'Repayment',calendar:'Due Calendar',
  settlement:'Settlement',collection:'Collections',alerts:'Alerts',documents:'Documents',settings:'Settings',support:'Support'
};
function showPage(id,label){
  pages.forEach(p=>p.classList.toggle('activePage',p.id===id));
  navs.forEach(n=>n.classList.toggle('active',n.dataset.page===id));
  const title=document.getElementById('pageTitle');
  if(title) title.textContent=label||titles[id]||id;
  history.replaceState(null,'','#'+id);
}
navs.forEach(n=>n.addEventListener('click',()=>showPage(n.dataset.page,n.textContent.trim())));
const initial=(location.hash||'#dashboard').slice(1);
showPage(titles[initial]?initial:'dashboard');
