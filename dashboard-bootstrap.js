(function(){
  const dash=document.getElementById('dashboard');
  if(!dash)return;
  const renderDemo=()=>{
    if(dash.children.length||!window.DirectCreditData||!window.DirectCreditData.demoReporting||!window.__dcRenderDashboard)return false;
    const data=window.DirectCreditData.demoReporting();
    data.source='demo';
    window.__dcRenderDashboard(data);
    return true;
  };
  const started=Date.now();
  const timer=setInterval(()=>{
    if(dash.children.length){clearInterval(timer);return;}
    if(renderDemo()||Date.now()-started>5000)clearInterval(timer);
  },250);
})();
