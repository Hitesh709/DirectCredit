(()=>{
  const picker=document.getElementById('applicationPicker');
  const list=document.getElementById('applicationPickerList');
  const search=document.getElementById('applicationSearch');
  const count=document.getElementById('pickerCount');
  const tabs=[...document.querySelectorAll('.summary-tab')];
  let rows=[];
  let activeStatus='all';
  const money=v=>Number(v||0).toLocaleString('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0});
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=v=>String(v??'').trim().toLowerCase().replace(/[\s-]+/g,'_');

  function statusOf(r){
    const s=norm(r.status||r.loan_status||r.stage||r.current_stage);
    if(['rejected','reject','declined','decline'].includes(s))return 'rejected';
    if(['pending','submitted','assessment','manual_review','under_review','review'].includes(s))return 'pending';
    if(['approved','approve','sanctioned','sanction','active','servicing','disbursed','repaid','overdue'].includes(s))return 'approved';
    return Number(r.sanctioned_amount||0)>0?'approved':'pending';
  }
  function sanctionedOf(r){return Number(r.sanctioned_amount||0)>0 || ['sanctioned','disbursed','active','servicing','repaid','overdue'].includes(norm(r.status||r.stage));}
  function approvalEligible(r){return statusOf(r)!=='rejected';}

  function buildRows(reporting){
    const loanRows=Array.isArray(reporting?.loan_records)?reporting.loan_records:[];
    if(loanRows.length)return loanRows.map(r=>({...r,customer_id:r.customer_id,customer_name:r.customer_name||'Customer',business_name:r.business_name||'',application_id:r.loan_id??r.id,status:r.status||r.stage,source:reporting?.source==='demo'?'demo':(r.source||'live')}));
    const customerRows=Array.isArray(reporting?.customer_records)?reporting.customer_records:[];
    return customerRows.map(c=>({...c,customer_id:c.customer_id??c.id,customer_name:c.customer_name||c.name,source:reporting?.source==='demo'?'demo':(c.source||'live')}));
  }

  function mergeDemo(list){
    const demo=window.DirectCreditData?.demoCustomers||[];
    const mapped=demo.map(c=>({customer_id:c.id,customer_name:c.name,business_name:c.business_name,application_id:c.loan?.id,requested_amount:c.loan?.requested_amount,eligible_amount:c.loan?.eligible_amount,sanctioned_amount:c.loan?.sanctioned_amount,disbursed_amount:c.loan?.disbursed_amount,outstanding_amount:c.loan?.outstanding_amount,status:c.loan?.status,stage:c.loan?.current_stage,source:'demo',customer_code:c.customer_code}));
    const existingDemoKeys=new Set(list.filter(r=>r.source==='demo').map(r=>String(r.customer_id)+':'+String(r.application_id))); return [...list,...mapped.filter(r=>!existingDemoKeys.has(String(r.customer_id)+':'+String(r.application_id)))];
  }

  function num(...values){
    for(const v of values){const n=Number(v);if(Number.isFinite(n))return n;}
    return 0;
  }

  function setSummary(reporting={}){
    const base=rows;
    const total=base.length;
    const rowApproved=base.filter(r=>statusOf(r)==='approved').length;
    const rowPending=base.filter(r=>statusOf(r)==='pending').length;
    const rowRejected=base.filter(r=>statusOf(r)==='rejected').length;
    const approved=rowApproved;
    const pending=rowPending;
    const rejected=rowRejected;
    const approvalRaw=reporting.approval_rate ?? reporting.approval_percent ?? reporting.approval_percentage;
    const approval=approvalRaw!==undefined && approvalRaw!==null ? Number(approvalRaw) : (total?approved/total*100:0);
    const rowSanctioned=base.reduce((s,r)=>s+Number(r.sanctioned_amount||0),0);
    const sanctioned=rowSanctioned;
    document.getElementById('summaryTotal').textContent=total.toLocaleString('en-IN');
    document.getElementById('summaryApproved').textContent=approved.toLocaleString('en-IN');
    document.getElementById('summaryPending').textContent=pending.toLocaleString('en-IN');
    document.getElementById('summaryRejected').textContent=rejected.toLocaleString('en-IN');
    document.getElementById('summaryApproval').textContent=`${Number.isFinite(approval)?approval.toFixed(1):'0.0'}%`;
    document.getElementById('summarySanctioned').textContent=money(sanctioned);
  }

  function matches(r,term){if(!term)return true;const hay=[r.customer_name,r.customer_code,r.business_name,r.application_id,r.mobile,r.email,r.status,r.stage].join(' ').toLowerCase();return hay.includes(term.toLowerCase());}
  function filtered(){const term=search?.value.trim()||'';return rows.filter(r=>{let ok=true;if(activeStatus==='approved')ok=statusOf(r)==='approved';else if(activeStatus==='pending')ok=statusOf(r)==='pending';else if(activeStatus==='rejected')ok=statusOf(r)==='rejected';else if(activeStatus==='approval')ok=approvalEligible(r);else if(activeStatus==='sanctioned')ok=sanctionedOf(r);return ok&&matches(r,term);});}

  function renderList(){
    const data=filtered();
    count.textContent=`${data.length} customer${data.length===1?'':'s'}`;
    if(!data.length){list.innerHTML='<div class="picker-empty">No applications match this selection.</div>';return;}
    list.innerHTML=data.map((r,i)=>{const stage=r.status||r.stage||'Pending';const amount=r.sanctioned_amount||r.requested_amount||r.eligible_amount||0;return `<button class="picker-row" type="button" data-row-index="${i}"><span class="picker-main"><span class="picker-name">${esc(r.customer_name||'Customer')}</span><span class="picker-sub">${esc(r.business_name||'')} ${r.application_id?'• Application #'+esc(r.application_id):''} ${r.customer_code?'• '+esc(r.customer_code):''}</span></span><span class="picker-meta"><span class="picker-stage">${esc(stage)}</span><span class="picker-amount">${money(amount)}</span></span></button>`;}).join('');
    [...list.querySelectorAll('.picker-row')].forEach(btn=>btn.addEventListener('click',()=>selectCustomer(data[Number(btn.dataset.rowIndex)])));
  }

  function openPicker(status){
    activeStatus=status||'all';tabs.forEach(t=>t.classList.toggle('active',t.dataset.status===activeStatus));
    const labels={all:'All Applications',approved:'Approved Applications',pending:'Pending Applications',rejected:'Rejected Applications',approval:'Applications Included in Approval',sanctioned:'Sanctioned Applications'};
    document.getElementById('pickerTitle').textContent=labels[activeStatus]||'Select Customer';
    document.getElementById('pickerSubtitle').textContent='Select a customer to open the full Customer, Contact, Banking, KYC, Risk and Eligibility workspace.';
    search.value='';renderList();picker.classList.add('open');picker.setAttribute('aria-hidden','false');setTimeout(()=>search.focus(),20);
  }
  function closePicker(){picker.classList.remove('open');picker.setAttribute('aria-hidden','true');}

  // Customer selection must work even when the live application selector has not
  // finished loading. The URL is the canonical selection state used by the
  // eligibility/customer workspace, so navigate directly instead of polling a
  // dynamically-created <select>. This also makes switching customers reliable
  // while already viewing the Eligibility tab.
  function selectCustomer(r){
    if(!r || r.customer_id===null || r.customer_id===undefined){
      console.warn('Applications: selected row has no customer_id',r);
      return;
    }
    const source=r.source==='demo'?'demo':'live';
    closePicker();
    const url=new URL(location.href);
    url.searchParams.set('customer_id',String(r.customer_id));
    url.searchParams.set('source',source);
    // Preserve the current customer workspace tab when possible. If the user
    // is selecting from a summary tab, start the newly selected customer on
    // Eligibility so the requested credit-decision view is immediately usable.
    url.searchParams.set('workspace_tab','eligibility');
    location.assign(url.toString());
  }

  async function loadSummary(){
    try{
      let reporting=null;
      if(window.DirectCreditData?.reporting)reporting=await window.DirectCreditData.reporting({force:true});
      rows=mergeDemo(buildRows(reporting));
      setSummary(reporting||{});
      renderList();
    }catch(e){
      rows=mergeDemo([]);
      setSummary({applications:rows.length});
      renderList();
      console.error('Applications summary load failed:',e);
    }
  }

  tabs.forEach(t=>t.addEventListener('click',()=>openPicker(t.dataset.status)));
  document.querySelectorAll('[data-picker-close]').forEach(x=>x.addEventListener('click',closePicker));
  search.addEventListener('input',renderList);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&picker.classList.contains('open'))closePicker()});
  document.getElementById('refreshBtn')?.addEventListener('click',()=>loadSummary());

  // Multi-step customer-to-loan journey.
  let journeyStep=0;
  const journeyPanels=[...document.querySelectorAll('.dc-journey-panel')];
  const journeySteps=[...document.querySelectorAll('.dc-journey-step')];
  const journeyBack=document.getElementById('dcJourneyBack');
  const journeyNext=document.getElementById('dcJourneyNext');
  const journeySubmit=document.getElementById('newApplicationSubmit');
  const journeyProgress=document.getElementById('dcJourneyProgress');
  const journeyReview=document.getElementById('dcJourneyReview');
  const journeyForm=document.getElementById('newApplicationForm');
  function showJourneyStep(index){
    journeyStep=Math.max(0,Math.min(6,index));
    journeyPanels.forEach((p,i)=>p.classList.toggle('active',i===journeyStep));
    journeySteps.forEach((b,i)=>{b.classList.toggle('active',i===journeyStep);b.classList.toggle('complete',i<journeyStep);});
    if(journeyBack)journeyBack.disabled=journeyStep===0;
    if(journeyNext)journeyNext.hidden=journeyStep===6;
    if(journeySubmit)journeySubmit.hidden=journeyStep!==6;
    if(journeyProgress)journeyProgress.style.width=((journeyStep+1)/7*100)+'%';
    if(journeyStep===6)buildJourneyReview();
    const content=document.querySelector('.dc-journey-content');if(content)content.scrollTop=0;
  }
  function buildJourneyReview(){
    if(!journeyReview||!journeyForm)return;
    const fd=new FormData(journeyForm);
    const rows=[['Customer',fd.get('name')],['Mobile',fd.get('mobile')],['Email',fd.get('email')],['PAN',fd.get('pan')],['Current address',[fd.get('current_address'),fd.get('current_city'),fd.get('state'),fd.get('pincode')].filter(Boolean).join(', ')],['Business',fd.get('business_name')],['Business type',fd.get('business_type')],['Monthly income',fd.get('monthly_income')?money(fd.get('monthly_income')):'Not entered'],['Bank',fd.get('bank_name')],['IFSC',fd.get('ifsc')],['Documents selected',[...journeyForm.querySelectorAll('input[type=file]')].filter(x=>x.files?.length).map(x=>x.files[0].name).join(', ')||'None yet'],['Loan product',fd.get('product')],['Requested amount',fd.get('requested_amount')?fmt(fd.get('requested_amount')):'Not entered'],['Tenure',(fd.get('tenure_months')||'6')+' months'],['Purpose',fd.get('loan_purpose')],['Customer consent',fd.get('customer_consent')?'Confirmed':'Not confirmed']];
    journeyReview.innerHTML='<div class="dc-review-grid">'+rows.map(([k,v])=>'<div><small>'+esc(k)+'</small><strong>'+esc(v||'—')+'</strong></div>').join('')+'</div>';
  }
  function validateJourneyStep(){
    const panel=journeyPanels[journeyStep];if(!panel)return true;
    const fields=[...panel.querySelectorAll('input,select,textarea')].filter(el=>el.type!=='file'&&el.type!=='checkbox'&&el.willValidate);
    for(const field of fields){if(!field.checkValidity()){field.reportValidity();field.focus();return false;}}
    if(journeyStep===0){
      const mobile=String(journeyForm.elements.mobile.value||'').replace(/\\D/g,'');
      if(mobile.length<10){alert('Enter a valid customer mobile number.');journeyForm.elements.mobile.focus();return false;}
    }
    if(journeyStep===3){
      const account=String(journeyForm.elements.account_number.value||'').trim();
      const confirm=String(journeyForm.elements.account_number_confirm.value||'').trim();
      if(account&&account!==confirm){alert('Bank account number and confirmation do not match.');journeyForm.elements.account_number_confirm.focus();return false;}
    }
    if(journeyStep===4){
      for(const fileInput of panel.querySelectorAll('input[type=file]'))if(fileInput.files?.[0]&&fileInput.files[0].size>2*1024*1024){alert(fileInput.files[0].name+' is larger than 2 MB.');return false;}
    }
    if(journeyStep===5){
      const amount=Number(journeyForm.elements.requested_amount.value);
      if(!Number.isFinite(amount)||amount<5000||amount>15000){alert('Enter a loan amount between ₹5,000 and ₹15,000.');journeyForm.elements.requested_amount.focus();return false;}
    }
    return true;
  }
  journeyNext?.addEventListener('click',()=>{if(validateJourneyStep())showJourneyStep(journeyStep+1);});
  journeyBack?.addEventListener('click',()=>showJourneyStep(journeyStep-1));
  journeySteps.forEach(b=>b.addEventListener('click',()=>{const target=Number(b.dataset.step);if(target<=journeyStep){showJourneyStep(target);return;}if(validateJourneyStep())showJourneyStep(target);}));
  journeyForm?.querySelector('[name="same_address"]')?.addEventListener('change',e=>{if(e.target.value==='yes')journeyForm.elements.permanent_address.value=[journeyForm.elements.current_address.value,journeyForm.elements.current_city.value,journeyForm.elements.state.value,journeyForm.elements.pincode.value].filter(Boolean).join(', ');});
  ['current_address','current_city','state','pincode'].forEach(n=>journeyForm?.elements[n]?.addEventListener('change',()=>{if(journeyForm.elements.same_address.value==='yes')journeyForm.elements.permanent_address.value=[journeyForm.elements.current_address.value,journeyForm.elements.current_city.value,journeyForm.elements.state.value,journeyForm.elements.pincode.value].filter(Boolean).join(', ');}));
  // Admin-created customer and application workflow.
  const newModal=document.getElementById('newApplicationModal');
  const newForm=document.getElementById('newApplicationForm');
  const newMessage=document.getElementById('newApplicationMessage');
  const newSubmit=document.getElementById('newApplicationSubmit');
  function closeNewApplication(){newModal?.classList.remove('open');newModal?.setAttribute('aria-hidden','true');}
  function openNewApplication(){newMessage.textContent='';newMessage.className='new-application-message';newForm?.reset();showJourneyStep(0);newModal?.classList.add('open');newModal?.setAttribute('aria-hidden','false');newForm?.querySelector('[name="name"]')?.focus();}
  document.getElementById('newApplicationBtn')?.addEventListener('click',openNewApplication);
  document.querySelectorAll('[data-new-app-close]').forEach(el=>el.addEventListener('click',closeNewApplication));
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&newModal?.classList.contains('open'))closeNewApplication();});
  const readDocument=async(file)=>{
    if(!file)return null;
    if(file.size>2*1024*1024)throw new Error(file.name+' is larger than 2 MB. Choose a smaller file.');
    if(!['application/pdf','image/jpeg','image/png'].includes(file.type))throw new Error(file.name+': only PDF, JPG and PNG files are supported.');
    return await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve({file_name:file.name,mime_type:file.type,file_size:file.size,data_url:String(reader.result)});reader.onerror=()=>reject(new Error('Could not read '+file.name));reader.readAsDataURL(file);});
  };
  newForm?.addEventListener('submit',async e=>{
    e.preventDefault();
    const form=new FormData(newForm);
    const name=String(form.get('name')||'').trim();
    const amount=Number(form.get('requested_amount'));
    const tenure=Number(form.get('tenure_months')||6);
    if(!name||!Number.isFinite(amount)||amount<5000||amount>15000){newMessage.textContent='Enter a customer name and a loan amount between ₹5,000 and ₹15,000.';newMessage.className='new-application-message show error';return;}
    const api=window.DirectCreditData;
    if(!api?.base||typeof api.headers!=='function'){newMessage.textContent='The DirectCredit API configuration is unavailable. Refresh the page and try again.';newMessage.className='new-application-message show error';return;}
    const headers={...api.headers(),'Content-Type':'application/json'};
    const payload={name,mobile:String(form.get('mobile')||'').trim()||null,email:String(form.get('email')||'').trim()||null,business_name:String(form.get('business_name')||'').trim()||null,business_type:String(form.get('business_type')||'').trim()||null,current_city:String(form.get('current_city')||'').trim()||null,monthly_income:Number(form.get('monthly_income')||0),customer_type:String(form.get('customer_type')||'Individual'),occupation:String(form.get('occupation')||'Business'),pan:String(form.get('pan')||'').trim().toUpperCase()||null,date_of_birth:String(form.get('date_of_birth')||'')||null,gender:String(form.get('gender')||'')||null,marital_status:String(form.get('marital_status')||'')||null,address:String(form.get('current_address')||'').trim()||null,permanent_address:String(form.get('permanent_address')||'').trim()||null,residence_ownership:String(form.get('residence_ownership')||'')||null,residence_since:String(form.get('residence_since')||'')||null,state:String(form.get('state')||'')||null,pincode:String(form.get('pincode')||'')||null,father_spouse_name:String(form.get('father_spouse_name')||'').trim()||null,monthly_turnover:Number(form.get('monthly_turnover')||0)||null,annual_turnover:Number(form.get('annual_turnover')||0)||null,existing_emi:Number(form.get('existing_emi')||0),dependents:Number(form.get('dependents')||0),gstin:String(form.get('gstin')||'').trim().toUpperCase()||null,business_address:String(form.get('business_address')||'').trim()||null,bank_name:String(form.get('bank_name')||'').trim()||null,account_holder_name:String(form.get('account_holder_name')||'').trim()||null,account_number:String(form.get('account_number')||'').trim()||null,ifsc:String(form.get('ifsc')||'').trim().toUpperCase()||null,account_type:String(form.get('account_type')||'')||null,average_bank_balance:Number(form.get('average_bank_balance')||0)||null,customer_consent:form.get('customer_consent')==='on'};
    const docTypes=[['pan_document','PAN'],['address_document','ADDRESS_PROOF'],['bank_document','BANK_STATEMENT'],['business_document','BUSINESS_PROOF'],['income_document','INCOME_PROOF'],['other_document','OTHER']];
    newSubmit.disabled=true;newSubmit.textContent='Creating…';newMessage.textContent='Checking documents and creating customer/application…';newMessage.className='new-application-message show';
    try{
      const docs=[];
      for(const [field,type] of docTypes){const file=form.get(field);if(file instanceof File&&file.size)docs.push({type,...await readDocument(file)});}
      // Preflight the authenticated loan route before creating a customer, avoiding orphan records.
      const authCheck=await fetch(api.base+'/admin/reports/customer/1/profile',{headers:api.headers(),cache:'no-store'});
      if(authCheck.status===401||authCheck.status===403)throw new Error('The configured API session is not authorized to create applications. Please sign in as an authorized administrator; no customer was created.');
      if(!authCheck.ok)throw new Error('Could not verify admin access (HTTP '+authCheck.status+'). No customer was created.');
      const customerResponse=await fetch(api.base+'/customers',{method:'POST',headers,body:JSON.stringify(payload)});
      const customerBody=await customerResponse.json().catch(()=>({}));
      if(!customerResponse.ok)throw new Error(customerBody.detail||customerBody.message||('Customer creation failed (HTTP '+customerResponse.status+').'));
      const customerId=customerBody.id;
      if(!customerId)throw new Error('Customer was saved but the API did not return a customer ID. Please check the customer list before retrying.');
      const loanResponse=await fetch(api.base+'/loans',{method:'POST',headers,body:JSON.stringify({customer_id:Number(customerId),requested_amount:amount,product:String(form.get('product')||'Micro Business Loan'),tenure_months:tenure,loan_purpose:String(form.get('loan_purpose')||'')||null,preferred_disbursement_date:String(form.get('preferred_disbursement_date')||'')||null,repayment_frequency:String(form.get('repayment_frequency')||'Monthly'),application_notes:String(form.get('application_notes')||'').trim()||null})});
      const loanBody=await loanResponse.json().catch(()=>({}));
      if(!loanResponse.ok)throw new Error('Customer created (ID '+customerId+'), but loan creation failed: '+(loanBody.detail||loanBody.message||('HTTP '+loanResponse.status))+'. Open that customer and retry the loan only; do not create the customer again.');
      const loanId=loanBody.id||loanBody.loan_id||null;
      for(const doc of docs){
        // The existing document API stores document records and their storage_key; keep files small.
        const documentPayload={customer_id:Number(customerId),loan_id:loanId?Number(loanId):null,document_type:doc.type,document_role:'supporting',file_name:doc.file_name,mime_type:doc.mime_type,file_size:doc.file_size,source:'admin_application',required:false,verification_status:'pending',storage_provider:'database',storage_key:doc.data_url};
        const response=await fetch(api.base+'/documents',{method:'POST',headers,body:JSON.stringify(documentPayload)});
        const body=await response.json().catch(()=>({}));
        if(!response.ok)throw new Error('Application created, but document "'+doc.file_name+'" could not be saved: '+(body.detail||body.message||('HTTP '+response.status))+'. Customer ID: '+customerId+', application ID: '+(loanId||'created')+'.');
      }
      newMessage.textContent='Customer and application created successfully'+(docs.length?' with '+docs.length+' document(s)':'')+'. Opening the customer workspace…';newMessage.className='new-application-message show success';
      await loadSummary();
      setTimeout(()=>{const url=new URL(location.href);url.searchParams.set('customer_id',String(customerId));url.searchParams.set('source','live');url.searchParams.set('workspace_tab','eligibility');location.assign(url.toString());},700);
    }catch(err){newMessage.textContent=err.message||'Unable to create application. Please check API access and try again.';newMessage.className='new-application-message show error';}
    finally{newSubmit.disabled=false;newSubmit.textContent='Create application';}
  });

  setSummary({applications:0,approved:0,pending:0,rejected:0,approval_rate:0,sanctioned_amount:0});
  loadSummary();
})();