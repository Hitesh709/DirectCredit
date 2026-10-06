(()=>{
  const removeReferenceCoverage=()=>{
    document.querySelectorAll('#applicationView .live-card').forEach(card=>{
      const h=card.querySelector('h3');
      if(h && h.textContent.trim().toUpperCase()==='REFERENCE FIELD COVERAGE') card.remove();
    });
  };
  const fit=()=>{
    document.documentElement.style.height='auto';
    document.body.style.height='auto';
    document.body.style.minHeight='0';
    document.body.style.overflow='visible';
    removeReferenceCoverage();
    const view=document.getElementById('applicationView');
    if(view){
      view.style.minHeight='0';
      view.style.height='auto';
    }
  };
  const boot=()=>{
    fit();
    const view=document.getElementById('applicationView');
    if(view){
      new MutationObserver(()=>requestAnimationFrame(fit)).observe(view,{childList:true,subtree:true});
    }
    document.querySelectorAll('.application-tab').forEach(tab=>tab.addEventListener('click',()=>setTimeout(fit,30)));
    window.addEventListener('resize',fit);
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();
