(async function(){
 const el=document.getElementById('slab');if(!el)return;const fmt=v=>'₹'+Number(v||0).toLocaleString('en-IN',{maximumFractionDigits:2});
 try{const d=await getReporting();el.innerHTML=`__PLACEHOLDER__`;
 }catch(e){el.innerHTML='<div class="slab-table-wrap"><h3>Reporting data unavailable</h3><p>Live database is unavailable; the reporting service may be offline.</p></div>';}
})();