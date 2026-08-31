const API_BASE = localStorage.getItem('directcredit_api_url') || (window.DIRECTCREDIT_API_URL || '');
const customerId = Number(new URLSearchParams(window.location.search).get('customer_id') || localStorage.getItem('directcredit_customer_id') || 1);

async function loadCustomerProfile(){
  if(!API_BASE) return; // Static reference view remains available until the API URL is configured.
  try{
    const res=await fetch(`${API_BASE}/api/customers/${customerId}/profile`);
    if(!res.ok) throw new Error('Profile unavailable');
    const data=await res.json();
    localStorage.setItem('directcredit_customer_id', String(customerId));
    renderProfile(data);
  }catch(err){ console.warn('DirectCredit profile API:',err.message); }
}

const money=v=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(Number(v||0));
const setText=(el,v)=>{if(el) el.textContent=v ?? '—';};

function renderProfile(data){
  const c=data.customer||{}, m=data.metrics||{};
  const nameEl=document.querySelector('.customer-main h2');
  if(nameEl){ nameEl.childNodes[0].textContent=(c.name||'Customer')+' '; }
  const strong=document.querySelector('.customer-main strong'); setText(strong,`CUST${String(c.id||customerId).padStart(8,'0')}`);
  const avatar=document.querySelector('.avatar'); if(avatar) avatar.textContent=(c.name||'C').split(/\s+/).map(x=>x[0]).join('').slice(0,2).toUpperCase();
  const metrics=document.querySelectorAll('.metric');
  [[m.total_loans||0],[money(m.total_loan_amount)],[money(m.outstanding_amount)],[money(m.amount_paid)],[m.credit_score||0]].forEach((v,i)=>setText(metrics[i]?.querySelector('strong'),v[0]));

  // Replace the reference profile values with the single backend customer record.
  const labels=[...document.querySelectorAll('.contact-list label')];
  const values={"Mobile Number":c.mobile,"Email Address":c.email,"Address":c.address,"Current City":c.current_city,"Business Name":c.business_name,"Business Type":c.business_type,"Date of Birth":c.date_of_birth,"PAN Number":c.pan,"Aadhaar Number":c.aadhaar_masked,"Marital Status":c.marital_status};
  labels.forEach(label=>{const row=label.parentElement; const b=row?.querySelector('b'); if(b && Object.prototype.hasOwnProperty.call(values,label.textContent.trim())) setText(b,values[label.textContent.trim()]||'—');});

  const summary={"Occupation":c.occupation,"Monthly Income":money(c.monthly_income),"Work Experience":`${c.work_experience_years||0} Years`,"Years in Business":`${c.years_in_business||0} Years`,"Average Bank Balance":money(c.average_bank_balance),"Primary Bank":c.primary_bank,"CIBIL Score":`${c.cibil_score||0} / 900`,`FOIR`: `${Number(c.foir||0).toFixed(2)}%`,"Existing EMI":money(c.existing_emi),"Dependents":c.dependents};
  document.querySelectorAll('.two-col label').forEach(label=>{const key=label.childNodes[0]?.textContent?.trim(); if(summary[key]!==undefined) setText(label.querySelector('b'),summary[key]);});

  const loanRows=document.querySelectorAll('.bottom-grid .table-panel:first-child tbody tr');
  (data.loans||[]).slice(0,loanRows.length).forEach((l,i)=>{const cells=loanRows[i].children; [l.id,l.product,money(l.sanctioned_amount),money(l.outstanding_amount),money(l.monthly_emi),l.tenure_months+' Months',l.status].forEach((v,j)=>setText(cells[j],v));});
  const docRows=document.querySelectorAll('.docs tbody tr');
  (data.documents||[]).slice(0,docRows.length).forEach((d,i)=>{setText(docRows[i].children[0],`▧  ${d.document_type}`);setText(docRows[i].children[1],d.verification_status);});
}

document.querySelectorAll('.profile-tabs button,.sub-tabs button').forEach(button=>button.addEventListener('click',()=>{const group=button.parentElement;group.querySelectorAll('button').forEach(b=>b.classList.remove('active'));button.classList.add('active')}));
document.querySelectorAll('.profile-tabs button').forEach((button,i)=>button.addEventListener('click',()=>{if(i===1)window.location.href=`number-contact.html?customer_id=${customerId}`;if(i===2)window.location.href=`bank-analysis.html?customer_id=${customerId}`;if(i===3)window.location.href=`kyc-employment.html?customer_id=${customerId}`;if(i===4)window.location.href=`risk-score.html?customer_id=${customerId}`}));
document.querySelectorAll('.head-actions button').forEach((button,i)=>button.addEventListener('click',()=>{if(i===0)alert('Edit Profile mode opened. Changes should be saved through the DirectCredit API.');if(i===1)window.print();if(i===2)alert('More customer profile actions.')}));
document.querySelectorAll('.table-panel h3 a,.view-link').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const href=a.closest('section')?.classList.contains('docs')?'documents.html':a.closest('section')?.classList.contains('small-table')?'repayment.html':'loans.html';window.location.href=`${href}?customer_id=${customerId}`;}));
loadCustomerProfile();
