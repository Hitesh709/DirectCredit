const views=[...document.querySelectorAll('.page')];
const nav=[...document.querySelectorAll('.customer-nav button')];
const titles={home:'Customer Dashboard',apply:'Apply for Loan',application:'My Application',loans:'My Loans',repayment:'Repayment',documents:'My Documents',profile:'My Profile',support:'Support'};
function show(id){views.forEach(v=>v.classList.toggle('active',v.id===id));nav.forEach(n=>n.classList.toggle('active',n.dataset.page===id));document.getElementById('pageTitle').textContent=titles[id]||'Customer Dashboard';history.replaceState(null,'','#'+id)}
nav.forEach(n=>n.onclick=()=>show(n.dataset.page));
function login(){const mobile=document.getElementById('mobile').value.trim();if(!/^[0-9]{10}$/.test(mobile)){alert('Enter a valid 10-digit mobile number.');return}sessionStorage.setItem('dcCustomerLogin','1');document.getElementById('login').style.display='none';document.getElementById('portal').style.display='flex';show('home')}
function logout(){sessionStorage.removeItem('dcCustomerLogin');document.getElementById('portal').style.display='none';document.getElementById('login').style.display='grid'}
document.getElementById('loginBtn').onclick=login;document.getElementById('logoutBtn').onclick=logout;
if(sessionStorage.getItem('dcCustomerLogin')==='1'){document.getElementById('login').style.display='none';document.getElementById('portal').style.display='flex'}else{document.getElementById('login').style.display='grid';document.getElementById('portal').style.display='none'}
const start=location.hash.replace('#','');if(start&&titles[start])show(start);