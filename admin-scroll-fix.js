/* Legacy compatibility bridge.
 * The canonical iframe sizing now lives in app.js. Keeping a second
 * contentBottom/height calculator here caused competing iframe heights,
 * especially when Funnel & Matrix tabs changed their active panel.
 */
(function(){
  function sync(){
    try{ window.DCResizeAdminFrames?.(); }catch(e){}
  }
  sync();
  window.addEventListener('load',sync);
  window.addEventListener('resize',()=>setTimeout(sync,40));
  document.addEventListener('click',()=>setTimeout(sync,40));
})();
