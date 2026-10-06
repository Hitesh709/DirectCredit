(function(){
  function fixFrame(frame){
    if(!frame || !frame.contentDocument) return;
    var doc=frame.contentDocument, html=doc.documentElement, body=doc.body;
    if(!html || !body) return;
    var style=doc.getElementById('dc-scroll-fix');
    if(!style){
      style=doc.createElement('style');
      style.id='dc-scroll-fix';
      (doc.head||html).appendChild(style);
    }
    style.textContent='html,body{height:auto!important;min-height:0!important;overflow:visible!important}body{width:100%!important}.content,.application-workspace,.funnel-workspace,.settlement-page,.collection-page,#accounting,#settlement,#collection,main{height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important}.table-wrap,.table-container,.content-table{max-height:none!important;overflow:visible!important}';
    html.style.setProperty('height','auto','important');
    body.style.setProperty('height','auto','important');
    html.style.setProperty('overflow','visible','important');
    body.style.setProperty('overflow','visible','important');
    var measure=function(){
      var h=Math.ceil(Math.max(body.scrollHeight,body.offsetHeight,html.scrollHeight,html.offsetHeight));
      frame.style.setProperty('height',Math.max(160,h+8)+'px','important');
      frame.style.setProperty('max-height','none','important');
    };
    requestAnimationFrame(measure);
    setTimeout(measure,100);
    setTimeout(measure,400);
    setTimeout(measure,900);
    if(window.ResizeObserver){
      try{
        if(frame.__dcScrollObserver) frame.__dcScrollObserver.disconnect();
        frame.__dcScrollObserver=new ResizeObserver(measure);
        frame.__dcScrollObserver.observe(body);
        frame.__dcScrollObserver.observe(html);
      }catch(e){}
    }
  }
  function bind(frame){
    if(!frame || frame.__dcScrollBound) return;
    frame.__dcScrollBound=true;
    frame.addEventListener('load',function(){fixFrame(frame);setTimeout(function(){fixFrame(frame)},150);});
    if(frame.contentDocument) fixFrame(frame);
  }
  function scan(){document.querySelectorAll('.page iframe[data-src]').forEach(bind);}
  scan();
  document.addEventListener('click',function(){setTimeout(scan,0);setTimeout(scan,100);});
  window.addEventListener('resize',function(){setTimeout(scan,0);setTimeout(function(){document.querySelectorAll('.page iframe[data-src]').forEach(fixFrame)},120);});
})();
