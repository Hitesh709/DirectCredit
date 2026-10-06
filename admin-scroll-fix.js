(function(){
  function visible(el){
    if(!el || el.nodeType!==1) return false;
    var s=window.getComputedStyle(el),r=el.getBoundingClientRect();
    if(s.display==='none'||s.visibility==='hidden'||s.position==='fixed'||s.position==='sticky') return false;
    return r.width>0&&r.height>0;
  }
  function contentBottom(doc){
    var win=doc.defaultView||window;
    var nodes=doc.body?doc.body.querySelectorAll('*'):[];
    var max=0;
    for(var i=0;i<nodes.length;i++){
      var el=nodes[i];
      if(!visible(el)) continue;
      var tag=el.tagName;
      var text=(el.textContent||'').trim();
      var meaningful=text.length>0||/^(IMG|SVG|CANVAS|VIDEO|TABLE|FORM|INPUT|SELECT|TEXTAREA|BUTTON)$/.test(tag);
      if(!meaningful) continue;
      var r=el.getBoundingClientRect();
      var bottom=r.bottom+(win.scrollY||0);
      if(bottom>max) max=bottom;
    }
    if(!max && doc.body){
      max=Math.max(doc.body.scrollHeight,doc.documentElement.scrollHeight);
    }
    return Math.ceil(max);
  }
  function fixFrame(frame){
    if(!frame || !frame.contentDocument) return;
    var doc=frame.contentDocument,html=doc.documentElement,body=doc.body;
    if(!html||!body) return;
    var style=doc.getElementById('dc-scroll-fix');
    if(!style){
      style=doc.createElement('style');style.id='dc-scroll-fix';
      (doc.head||html).appendChild(style);
    }
    style.textContent='html,body{height:auto!important;min-height:0!important;overflow:visible!important}body{width:100%!important}.content,.application-workspace,.funnel-workspace,.settlement-page,.collection-page,#accounting,#settlement,#collection,main{height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important}.table-wrap,.table-container,.content-table{max-height:none!important;overflow:visible!important}';
    html.style.setProperty('height','auto','important');
    body.style.setProperty('height','auto','important');
    html.style.setProperty('overflow','visible','important');
    body.style.setProperty('overflow','visible','important');
    var measure=function(){
      var h=contentBottom(doc);
      if(!h) return;
      frame.style.setProperty('height',Math.max(120,h+24)+'px','important');
      frame.style.setProperty('max-height','none','important');
    };
    requestAnimationFrame(measure);
    setTimeout(measure,100);setTimeout(measure,400);setTimeout(measure,900);
    if(window.ResizeObserver){
      try{
        if(frame.__dcScrollObserver) frame.__dcScrollObserver.disconnect();
        frame.__dcScrollObserver=new ResizeObserver(measure);
        frame.__dcScrollObserver.observe(body);
      }catch(e){}
    }
  }
  function bind(frame){
    if(!frame||frame.__dcScrollBound)return;
    frame.__dcScrollBound=true;
    frame.addEventListener('load',function(){fixFrame(frame);setTimeout(function(){fixFrame(frame)},150);});
    if(frame.contentDocument)fixFrame(frame);
  }
  function scan(){document.querySelectorAll('.page iframe[data-src]').forEach(bind);}
  scan();
  document.addEventListener('click',function(){setTimeout(scan,0);setTimeout(scan,100);});
  window.addEventListener('resize',function(){setTimeout(scan,0);setTimeout(function(){document.querySelectorAll('.page iframe[data-src]').forEach(fixFrame)},120);});
})();
