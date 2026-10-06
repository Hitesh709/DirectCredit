(()=>{
  const TARGET='REFERENCE FIELD COVERAGE';
  const clean=()=>{
    const root=document.getElementById('applicationView');
    if(!root) return;
    root.querySelectorAll('.live-card').forEach(card=>{
      const heading=card.querySelector('h3');
      if(heading && heading.textContent.trim().toUpperCase()===TARGET){
        card.remove();
      }
    });
  };
  clean();
  new MutationObserver(clean).observe(document.getElementById('applicationView')||document.body,{childList:true,subtree:true});
})();
