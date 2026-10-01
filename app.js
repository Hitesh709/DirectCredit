(function(){
  const SIDEBAR_KEY='directcredit_sidebar_collapsed';
  const sidebar=document.getElementById('adminSidebar');
  const toggle=document.getElementById('sidebarToggle');
  const iconMap={dashboard:'⌂',reports:'▤',loanRequest:'▣',funnelMatrix:'▦',accounting:'$',collection:'⌖',settlement:'↔',documents:'▤',alerts:'!',settings:'⚙',support:'☎'};
  const setCollapsed=(collapsed,persist=true)=>{
    if(!sidebar||!toggle)return;
    document.body.classList.toggle('sidebar-collapsed',collapsed);
    toggle.setAttribute('aria-expanded',String(!collapsed));
    toggle.setAttribute('aria-label',collapsed?'Expand navigation':'Minimize navigation');
    toggle.title=collapsed?'Expand navigation':'Minimize navigation';
    toggle.querySelector('span').textContent=collapsed?'›':'‹';
    if(persist) localStorage.setItem(SIDEBAR_KEY,collapsed?'1':'0');
  };
  document.querySelectorAll('.nav[data-page]').forEach(n=>{n.dataset.icon=iconMap[n.dataset.page]||'•'});
  const saved=localStorage.getItem(SIDEBAR_KEY);
  setCollapsed(saved==='1',false);
  toggle?.addEventListener('click',()=>setCollapsed(!document.body.classList.contains('sidebar-collapsed')));
  window.DCAdminSidebar={setCollapsed,isCollapsed:()=>document.body.classList.contains('sidebar-collapsed')};
})();

const pages=[...document.querySelectorAll('.page')];
const navs=[...document.querySelectorAll('.nav')];
const titles={
  dashboard:'Dashboard',reports:'Analytics',loanRequest:'Applications',funnelMatrix:'Funnel & Matrix',
  accounting:'Accounting',settlement:'Settlement',collection:'Collections',alerts:'Alerts',documents:'Documents',settings:'Settings',support:'Support'
};
function showPage(id,label){
  pages.forEach(p=>p.classList.toggle('activePage',p.id===id));
  navs.forEach(n=>n.classList.toggle('active',n.dataset.page===id));
  document.body.classList.toggle('dc-iframe-page-active', ['loanRequest','funnelMatrix','accounting','settlement','collection'].includes(id));
  const activePage=document.getElementById(id);
  const frame=activePage?.querySelector('iframe[data-src]');
  if(frame && !frame.getAttribute('src')){
    frame.src=frame.dataset.src;
  }
  const title=document.getElementById('pageTitle');
  if(title) title.textContent=label||titles[id]||id;
  history.replaceState(null,'','#'+id);
}
navs.forEach(n=>n.addEventListener('click',()=>showPage(n.dataset.page,n.textContent.trim())));
const initial=(location.hash||'#dashboard').slice(1);
showPage(titles[initial]?initial:'dashboard');
