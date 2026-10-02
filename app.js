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

/* Keep embedded admin modules in the parent scroll container. The iframe itself
   is expanded to its same-origin document height so users get one scrollbar. */
function fitAdminFrame(frame){
  if(!frame||!frame.contentDocument)return;
  const doc=frame.contentDocument;
  const html=doc.documentElement, body=doc.body;
  if(!html||!body)return;
  html.style.overflow='hidden';
  body.style.overflow='hidden';
  const measure=()=>{
    const h=Math.max(html.scrollHeight,html.offsetHeight,body.scrollHeight,body.offsetHeight,body.getBoundingClientRect().height);
    frame.style.height=Math.max(120,h+2)+'px';
  };
  requestAnimationFrame(measure);
  setTimeout(measure,80);
  setTimeout(measure,350);
  if(window.ResizeObserver){
    try{
      if(frame.__dcResizeObserver)frame.__dcResizeObserver.disconnect();
      frame.__dcResizeObserver=new ResizeObserver(measure);
      frame.__dcResizeObserver.observe(body);
      frame.__dcResizeObserver.observe(html);
    }catch(e){}
  }
}
function prepareAdminFrame(frame){
  if(!frame)return;
  frame.style.width='100%';
  frame.style.display='block';
  frame.style.border='0';
  frame.style.overflow='hidden';
  frame.style.margin='0';
  frame.style.padding='0';
  frame.style.minHeight='0';
  frame.addEventListener('load',()=>fitAdminFrame(frame),{once:false});
  if(frame.contentDocument)fitAdminFrame(frame);
}
function showPage(id,label){
  pages.forEach(p=>p.classList.toggle('activePage',p.id===id));
  navs.forEach(n=>n.classList.toggle('active',n.dataset.page===id));
  document.body.classList.toggle('dc-iframe-page-active', ['loanRequest','funnelMatrix','accounting','settlement','collection'].includes(id));
  const activePage=document.getElementById(id);
  const frame=activePage?.querySelector('iframe[data-src]');
  if(frame){
    prepareAdminFrame(frame);
    if(!frame.getAttribute('src')) frame.src=frame.dataset.src;
    else fitAdminFrame(frame);
  }
  const title=document.getElementById('pageTitle');
  if(title) title.textContent=label||titles[id]||id;
  history.replaceState(null,'','#'+id);
}
navs.forEach(n=>n.addEventListener('click',()=>showPage(n.dataset.page,n.textContent.trim())));
const initial=(location.hash||'#dashboard').slice(1);
showPage(titles[initial]?initial:'dashboard');