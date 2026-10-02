(function(){
  const SIDEBAR_KEY='directcredit_sidebar_collapsed';
  const sidebar=document.getElementById('adminSidebar');
  const toggle=document.getElementById('sidebarToggle');
  const iconMap={dashboard:'⌂',reports:'▤',loanRequest:'▣',funnelMatrix:'▦',accounting:'$',collection:'⌖',settlement:'↔',documents:'▤',alerts:'!',settings:'⚙',support:'☎'};
  const setCollapsed=(collapsed,persist=true)=>{if(!sidebar||!toggle)return;document.body.classList.toggle('sidebar-collapsed',collapsed);toggle.setAttribute('aria-expanded',String(!collapsed));toggle.setAttribute('aria-label',collapsed?'Expand navigation':'Minimize navigation');toggle.title=collapsed?'Expand navigation':'Minimize navigation';const s=toggle.querySelector('span');if(s)s.textContent=collapsed?'›':'‹';if(persist)localStorage.setItem(SIDEBAR_KEY,collapsed?'1':'0')};
  document.querySelectorAll('.nav[data-page]').forEach(n=>{n.dataset.icon=iconMap[n.dataset.page]||'•'});
  setCollapsed(localStorage.getItem(SIDEBAR_KEY)==='1',false);
  toggle?.addEventListener('click',()=>setCollapsed(!document.body.classList.contains('sidebar-collapsed')));
  window.DCAdminSidebar={setCollapsed,isCollapsed:()=>document.body.classList.contains('sidebar-collapsed')};

  function injectReadableFrameStyle(doc){
    if(!doc||doc.getElementById('dc-frame-readable'))return;
    const style=doc.createElement('style');style.id='dc-frame-readable';
    style.textContent='html{font-size:16px!important;height:auto!important;min-height:0!important;overflow:visible!important}body{font-size:13px!important;line-height:1.5!important;height:auto!important;min-height:0!important;overflow:visible!important;-webkit-font-smoothing:antialiased!important}h1{font-size:26px!important;line-height:1.2!important}h2{font-size:20px!important;line-height:1.25!important}h3{font-size:16px!important;line-height:1.3!important}h4{font-size:14px!important}p{font-size:13px!important;line-height:1.5!important}label{font-size:12px!important}small{font-size:11px!important}th{font-size:11px!important}td{font-size:12px!important;line-height:1.4!important}button,input,select,textarea{font-size:12px!important}.page-head,.page-header,.header,.content-head{margin-top:0!important}.content,.application-workspace,.funnel-workspace,.settlement-page,.collection-page,#accounting,#settlement,#collection,main{padding-top:0!important;min-height:0!important;height:auto!important}.application-view{min-height:0!important;height:auto!important}.table-wrap,.table-container,.content-table{max-height:none!important;overflow:visible!important}';
    (doc.head||doc.documentElement).appendChild(style);
  }
  function fitAdminFrame(frame){
    if(!frame||!frame.contentDocument)return;
    const doc=frame.contentDocument,html=doc.documentElement,body=doc.body;if(!html||!body)return;
    injectReadableFrameStyle(doc);
    html.style.overflow='visible';body.style.overflow='visible';
    const measure=()=>{const h=Math.ceil(Math.max(body.scrollHeight,body.offsetHeight,html.scrollHeight,html.offsetHeight));frame.style.setProperty('height',Math.max(140,h+4)+'px','important')};
    requestAnimationFrame(measure);setTimeout(measure,80);setTimeout(measure,300);setTimeout(measure,800);
    if(window.ResizeObserver){try{if(frame.__dcResizeObserver)frame.__dcResizeObserver.disconnect();frame.__dcResizeObserver=new ResizeObserver(measure);frame.__dcResizeObserver.observe(body);frame.__dcResizeObserver.observe(html)}catch(e){}}
  }
  function prepareAdminFrame(frame){if(!frame)return;frame.style.width='100%';frame.style.display='block';frame.style.border='0';frame.style.overflow='hidden';frame.style.margin='0';frame.style.padding='0';frame.addEventListener('load',()=>fitAdminFrame(frame),{once:false});if(frame.contentDocument)fitAdminFrame(frame)}
  function fitAll(){document.querySelectorAll('.page iframe[data-src]').forEach(f=>{prepareAdminFrame(f);if(f.contentDocument?.readyState==='complete')fitAdminFrame(f)})}
  window.DCResizeAdminFrames=fitAll;

  const pages=[...document.querySelectorAll('.page')],navs=[...document.querySelectorAll('.nav')];
  const titles={dashboard:'Dashboard',reports:'Analytics',loanRequest:'Applications',funnelMatrix:'Funnel & Matrix',accounting:'Accounting',settlement:'Settlement',collection:'Collections',alerts:'Alerts',documents:'Documents',settings:'Settings',support:'Support'};
  function showPage(id,label){
    pages.forEach(p=>p.classList.toggle('activePage',p.id===id));
    navs.forEach(n=>n.classList.toggle('active',n.dataset.page===id));
    document.body.classList.toggle('dc-iframe-page-active',['loanRequest','funnelMatrix','accounting','settlement','collection'].includes(id));
    const activePage=document.getElementById(id),frame=activePage?.querySelector('iframe[data-src]');
    if(frame){prepareAdminFrame(frame);if(!frame.getAttribute('src'))frame.src=frame.dataset.src;else fitAdminFrame(frame)}
    const title=document.getElementById('pageTitle');if(title)title.textContent=label||titles[id]||id;
    const main=document.querySelector('.main');if(main)main.scrollTop=0;
    history.replaceState(null,'','#'+id);
  }
  navs.forEach(n=>n.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();showPage(n.dataset.page,n.textContent.trim())}));
  const initial=(location.hash||'#dashboard').slice(1);showPage(titles[initial]?initial:'dashboard');
  window.addEventListener('resize',fitAll);
})();
