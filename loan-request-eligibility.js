(()=> {
  const params=new URLSearchParams(location.search);
  const view=document.getElementById('applicationView');
  const tabs=['profile','contact','bank','kyc','risk','eligibility'];
  let selected='';
  let data=null;
  const money=v=>v===null||v===undefined||v===''?'Not available':`₹${Number(v).toLocaleString('en-IN',{maximumFractionDigits:2})}`;
  const val=(v,f='Not available')=>v===null||v===undefined||v===''?f:v;
  const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const labels={ownership_proof:'Ownership Proof',business_geography:'Business Geography',age:'Age',cibil_enquiries:'CIBIL Enquiries',cibil_repayment:'CIBIL Repayment',unsecured_track:'Unsecured Track',bank_credits:'Bank Credits',bank_stability:'Bank Statement Stability',aqb:'Average Quarterly Balance',emi_track:'EMI Repayment Track',business_type:'Business Type',business_vintage:'Business Vintage',business_stock:'Business Stock',monthly_emi:'Monthly EMI Obligation',foir:'FOIR',trade_validation:'Trade Validation',gst:'GST Registration',gstr3b:'GSTR-3B Turnover',itr:'ITR',mobile_stability:'Mobile Stability',both_owned_bonus:'Both-Owned Bonus'};
  const max={ownership_proof:5,business_geography:5,age:5,cibil_enquiries:5,cibil_repayment:15,unsecured_track:10,bank_credits:10,bank_stability:5,aqb:5,emi_track:5,business_type:5,business_vintage:5,business_stock:5,monthly_emi:5,foir:5,trade_validation:10,gst:5,gstr3b:10,itr:5,mobile_stability:5,both_owned_bonus:5};

  function card(title,rows){
    return `<div class="live-card"><h3>${esc(title)}</h3><div class="live-grid">${rows.map(r=>`<div><small>${esc(r[0])}</small><strong>${esc(val(r[1]))}</strong></div>`).join('')}</div></div>`;
  }
  function read(root, paths){
    for(const p of paths){
      const parts=p.split("."); let cur=root;
      for(const part of parts){ if(cur==null) break; cur=cur[part]; }
      if(cur!==null && cur!==undefined && cur!=="") return cur;
    }
    return null;
  }
  function refCard(title, fields, root){
    return card(title, fields.map(f=>[f[0],read(root,f[1])]));
  }
  function referenceDetails(d,key){
    const c=d.customer||{}, l=(d.loans||[])[0]||{}, b=d.bank_analysis||{}, k=d.kyc_employment||{}, r=d.risk_score||{};
    const root=Object.assign({},d,{customer:c,loan:l,bank:b,kyc:k,risk:r});
    const commonCustomer=[
      ["Customer ID",["customer.id"]],["Customer Code",["customer.customer_code"]],["Customer Name",["customer.name"]],
      ["Customer Type",["customer.customer_type"]],["Date of Birth",["customer.date_of_birth","customer.dob"]],["Gender",["customer.gender"]],
      ["Marital Status",["customer.marital_status"]],["Father / Spouse",["customer.father_spouse","customer.father_name","customer.spouse_name"]],
      ["Email ID",["customer.email"]],["Preferred Language",["customer.preferred_language"]],["Mobile Number",["customer.mobile"]],
      ["Alternate Mobile Number",["customer.alternate_mobile","customer.alt_mobile"]],["Current Address",["customer.address","customer.current_address"]],
      ["Residence Type",["customer.residence_ownership","customer.residence_type"]],["Current Pincode",["customer.current_pincode","address_details.pincode"]],
      ["Current State",["customer.current_state","address_details.state"]],["Current City",["customer.current_city","address_details.city"]],
      ["Residence Stability",["customer.residence_stability","kyc.residence_stability"]],["Living Since",["customer.residence_since","customer.living_since"]],
      ["PAN",["customer.pan"]],["Aadhaar",["customer.aadhaar_masked","customer.aadhaar"]],["KYC Status",["customer.kyc_status","kyc.kyc_status"]],
      ["Occupation",["customer.occupation","kyc.employment_type"]],["Business Name",["customer.business_name","business_details.firm_name"]],
      ["Business Type",["customer.business_type","business_details.business_type"]],["Business Vintage",["customer.years_in_business","kyc.years_in_business"]],
      ["Work Experience",["customer.work_experience_years","kyc.work_experience_years"]],["Monthly Income",["customer.monthly_income","kyc.income"]],
      ["Dependents",["customer.dependents","customer.dependent_count"]],["Primary Bank",["customer.primary_bank","financial_details.bank_name"]],
      ["CIBIL Score",["customer.cibil_score","risk.credit_score"]],["FOIR",["customer.foir"]],["Existing EMI",["customer.existing_emi"]]
    ];
    const contact=[
      ["Registered Mobile",["contact_details.registered_mobile","customer.mobile"]],["Alternate Mobile",["contact_details.alternate_mobile","customer.alternate_mobile"]],
      ["Registered Email",["contact_details.registered_email","customer.email"]],["Contact Score",["contact_details.contact_score","contact_score"]],
      ["Mobile Verification",["contact_details.mobile_verification","customer.mobile_verified"]],["Email Verification",["contact_details.email_verification","customer.email_verified"]],
      ["Address Type",["address_details.address_type"]],["Address Line 1",["address_details.address_line1","address_details.line1"]],
      ["Town",["address_details.town"]],["State",["address_details.state"]],["City",["address_details.city"]],
      ["District",["address_details.district"]],["Landmark",["address_details.landmark"]],["Pincode",["address_details.pincode","address_details.zipcode"]],
      ["Device",["contact_details.device_sim.device","contact_details.device_sim.device_name"]],["SIM Operator",["contact_details.device_sim.sim_operator","contact_details.device_sim.operator"]],
      ["SIM Type",["contact_details.device_sim.sim_type"]],["SIM Age",["contact_details.device_sim.sim_age"]],["Device Risk Score",["contact_details.device_sim.risk_score"]],
      ["Device Risk Status",["contact_details.device_sim.risk_status","contact_details.device_sim.status"]]
    ];
    const bank=[
      ["Account Holder",["bank.account_holder","customer.name"]],["Account Number",["bank.account_number","financial_details.account_number"]],
      ["IFSC Code",["bank.ifsc_code","financial_details.ifsc_code"]],["Bank Name",["bank.bank_name","customer.primary_bank"]],
      ["Branch Name",["bank.branch_name","financial_details.branch_name"]],["Account Type",["bank.account_type","financial_details.account_type"]],
      ["Statement Period",["bank.statement_period","bank.period"]],["Statement Days",["bank.statement_days"]],
      ["Total Credits",["bank.credits","bank.total_credits"]],["Total Debits",["bank.debits","bank.total_debits"]],
      ["Net Cash Flow",["bank.net_cash_flow"]],["Average Monthly Balance",["bank.average_monthly_balance","bank.average_eod_balance"]],
      ["Average Monthly Credit",["bank.average_monthly_credit"]],["Average Monthly Debit",["bank.average_monthly_debit"]],
      ["Total Transactions",["bank.total_transactions","bank.transactions"]],["Negative Balance Events",["bank.negative_balance_count","bank.negative_balance_events"]],
      ["Bank Analysis Status",["bank.status","bank.health"]],["Opening Balance",["bank.opening_balance"]],["Closing Balance",["bank.closing_balance"]],
      ["Average Credit",["bank.average_credit"]],["Average Debit",["bank.average_debit"]],["Highest Credit",["bank.highest_credit"]],["Highest Debit",["bank.highest_debit"]]
    ];
    const kyc=[
      ["KYC Status",["kyc.kyc_status","customer.kyc_status"]],["KYC Completed On",["kyc.kyc_completed_on"]],
      ["PAN Verification",["kyc.pan_status","kyc.pan_verified"]],["Aadhaar Verification",["kyc.aadhaar_status","kyc.aadhaar_verified"]],
      ["CKYC Status",["kyc.ckyc_status"]],["CRIF Status",["kyc.crif_status"]],["Overall KYC Score",["kyc.overall_kyc_score"]],
      ["Employment Type",["kyc.employment_type","customer.occupation"]],["Employer / Business",["kyc.employer_name","customer.business_name"]],
      ["Designation",["kyc.designation"]],["Net Monthly Income",["kyc.net_monthly_income","kyc.income"]],["Other Income",["kyc.other_income"]],
      ["No. of Workers",["business_details.no_of_workers","business_details.workers"]],["Total Salary",["business_details.total_salary"]],
      ["No. of Working Days",["business_details.working_days"]],["Visiting Card",["business_details.visiting_card"]],["Contract Based",["business_details.contract_based"]],
      ["Seller / Business Number",["business_details.seller_number","business_details.registration_number"]],["Seller Firm Name",["business_details.seller_firm_name","business_details.firm_name"]],
      ["Ownership",["business_details.ownership","customer.residence_ownership"]],["Products / Machinery / Stock",["business_details.products","business_details.stock"]],
      ["PD Status",["kyc.pd_status","kyc.pd_verification"]],["Sanction Check",["kyc.sanction_check","kyc.sanction_status"]],
      ["Ownership Proof",["kyc.ownership_proof_status","customer.ownership_proof_status"]],["Overall Status",["kyc.overall_status"]]
    ];
    const risk=[
      ["Overall Risk Score",["risk.total_score","directcredit_score"]],["Maximum Score",["risk.max_score"]],["Credit / CIBIL Score",["risk.credit_score"]],
      ["Risk Tier",["risk.risk_tier","risk.risk_grade"]],["Risk Category",["risk.category"]],["Score Status",["risk.score_status"]],
      ["Auto Decision",["risk.auto_decision","risk.decision"]],["Approval %",["risk.approval_percent"]],["Assessment Date",["risk.assessment_date","assessment_date"]],
      ["Scorecard Version",["risk.scorecard_version","risk.version"]],["Probability of Default",["risk.probability_default","risk.pd"]],
      ["Loss Given Default",["risk.loss_given_default","risk.lgd"]],["Expected Loss",["risk.expected_loss"]],["Recommended Limit",["risk.recommended_limit"]],
      ["Recommended Tenure",["risk.recommended_tenure"]],["Recommended Interest Rate",["risk.recommended_interest_rate"]]
    ];
    const eligibility=[
      ["Application ID",["loan.id","loan.application_id"]],["Application Date",["loan.application_date","loan.created_at"]],
      ["Loan Product",["loan.product","loan.loan_product"]],["Loan Purpose",["loan.loan_purpose","loan.purpose"]],
      ["Requested Amount",["loan.requested_amount"]],["Eligible Amount",["loan.eligible_amount","eligible_amount"]],
      ["Sanctioned Amount",["loan.sanctioned_amount"]],["Disbursed Amount",["loan.disbursed_amount"]],["Outstanding Amount",["loan.outstanding_amount"]],
      ["Requested Tenure",["loan.requested_tenure_months"]],["Tenure",["loan.tenure_months"]],["Interest Rate",["loan.interest_rate"]],
      ["Monthly EMI",["loan.monthly_emi"]],["Processing Fee",["loan.processing_fee"]],["Total Interest",["loan.total_interest"]],
      ["Total Repayment",["loan.total_repayment"]],["Next Due Date",["loan.next_due_date","loan.due_date"]],["Next Due Amount",["loan.next_due_amount"]],
      ["Eligibility Score",["loan.eligibility_score","risk.approval_percent"]],["Eligibility Status",["eligibility_status","loan.eligibility_status"]],
      ["Application Stage",["loan.current_stage","loan.stage"]],["Status",["loan.status"]],["Disbursement Date",["loan.disbursement_date"]]
    ];
    const groups={profile:commonCustomer,contact:contact,bank:bank,kyc:kyc,risk:risk,eligibility:eligibility};
    return refCard("REFERENCE FIELD COVERAGE",groups[key]||[],root);
  }

  function addEligibilityMicroDetails(c,l,k,risk){
    view.insertAdjacentHTML('beforeend',`
      <div class="live-micro-grid">
        ${card('RECOMMENDED OFFER',[
          ['Recommended Limit',money(l.eligible_amount)],
          ['Interest Rate',l.interest_rate==null?'Policy configured rate':l.interest_rate+'%'],
          ['Recommended Tenure',l.tenure_months?(l.tenure_months+' months'):'Not available'],
          ['Processing Fee','As configured by policy']
        ])}
        ${card('REQUIRED DOCUMENTS',[
          ['PAN Card','Required'],['Aadhaar / KYC','Required'],['Bank Statement','Required'],['GST / ITR','As applicable']
        ])}
        ${card('REPAYMENT CAPACITY',[
          ['Monthly Income',money(c.monthly_income)],['Existing EMI',money(c.existing_emi)],
          ['FOIR',c.foir==null?'Not available':c.foir+'%'],['Proposed EMI',money(l.monthly_emi)]
        ])}
        ${card('RISK INDICATORS',[
          ['CIBIL',risk.credit_score],['Decision',risk.decision],['Risk Tier',risk.risk_tier],
          ['Hard Rejects',(risk.hard_rejects||[]).length]
        ])}
        ${card('PROCESS TRACKER',[
          ['Application Submitted','Completed'],
          ['KYC Verification',k.kyc_status||'Pending'],
          ['Document Verification','Tracked'],
          ['Credit Assessment',risk.source==='scorecard'?'Completed':'Pending'],
          ['Eligibility Approval',risk.decision||'Pending'],
          ['Sanction',l.status||'Pending']
        ])}
      </div>`);
  }
  function render(key){
    if(!data){view.innerHTML='<div class="live-empty">Select an application to load data.</div>';return;}
    const c=data.customer||{}, loans=data.loans||[], l=loans[0]||{}, m=data.metrics||{}, bank=data.bank_analysis||{}, k=data.kyc_employment||{}, risk=data.risk_score||{};
    if(key==='profile'){
      view.innerHTML=card('Customer Profile',[
        ['Customer ID',c.id],['Customer Code',c.customer_code],['Name',c.name],['Customer Type',c.customer_type],
        ['Business',c.business_name],['Business Type',c.business_type],['Occupation',c.occupation],['City',c.current_city]
      ]);
    } else if(key==='contact'){
      view.innerHTML=card('Number & Contact Details',[
        ['Mobile',c.mobile],['Email',c.email],['Current Address',c.address],['Permanent Address',c.permanent_address],
        ['Email Verification',c.email_verified],['Residence Ownership',c.residence_ownership],['Residence Since',c.residence_since]
      ]);
    } else if(key==='bank'){
      view.innerHTML=card('Bank Statement Analysis',[
        ['Primary Bank',c.primary_bank],['Average EOD Balance',money(bank.average_eod_balance)],
        ['Avg Monthly Credit',money(bank.average_monthly_credit)],['Avg Monthly Debit',money(bank.average_monthly_debit)],
        ['Transactions',bank.total_transactions],['Negative Balance Events',bank.negative_balance_count],
        ['Outstanding',money(m.outstanding_amount)],['Overdue',money(m.overdue_amount)],['Data Status',bank.status]
      ]);
    } else if(key==='kyc'){
      view.innerHTML=card('KYC & Employment',[
        ['KYC Status',k.kyc_status],['Occupation',k.employment_type],
        ['Monthly Income',k.income==null?null:money(k.income)],
        ['Business Vintage',c.years_in_business==null?null:`${c.years_in_business} years`],
        ['Work Experience',c.work_experience_years==null?null:`${c.work_experience_years} years`],
        ['Residence Ownership',k.residence_ownership],['Ownership Proof',k.ownership_proof_status]
      ]);
    } else if(key==='risk'){
      const factors=risk.factor_scores||{};
      const factorRows=Object.entries(factors).map(([name,points])=>[labels[name]||name,`${points} / ${max[name]??'-'}`]);
      view.innerHTML=
        card('Risk & Score Breakdown',[
          ['DirectCredit Score',data.directcredit_score??risk.total_score],
          ['Maximum Score',risk.max_score||125],['Raw Score',risk.raw_score??risk.total_score],
          ['Scorecard Version',risk.scorecard_version||risk.version],['Risk Tier',risk.risk_tier],
          ['Decision',risk.decision],['Approval',risk.approval_percent==null?'Not applicable':risk.approval_percent+'%'],
          ['CIBIL Score',risk.credit_score],['FOIR',c.foir==null?null:c.foir+'%'],
          ['Existing EMI',c.existing_emi==null?null:money(c.existing_emi)]
        ])+
        (factorRows.length?card('125-Point Factor Breakdown',factorRows):card('125-Point Factor Breakdown',[['Status','No completed scorecard assessment']]))+
        (risk.hard_rejects?.length?`<div class="live-card"><h3>Hard Reject Reasons</h3><ul>${risk.hard_rejects.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>`:'')+
        (risk.reasons?.length?`<div class="live-card"><h3>Assessment Reasons</h3><ul>${risk.reasons.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div>`:'');
    } else {
      view.innerHTML=card('Loan Request & Eligibility',[
        ['Latest Loan ID',l.id],['Requested Amount',l.requested_amount==null?null:money(l.requested_amount)],
        ['Eligible Amount',l.eligible_amount==null?null:money(l.eligible_amount)],
        ['Sanctioned Amount',l.sanctioned_amount==null?null:money(l.sanctioned_amount)],
        ['Disbursed Amount',l.disbursed_amount==null?null:money(l.disbursed_amount)],
        ['Monthly EMI',l.monthly_emi==null?null:money(l.monthly_emi)],
        ['Tenure',l.tenure_months?`${l.tenure_months} months`:null],['Interest Rate',l.interest_rate==null?null:l.interest_rate+'%'],
        ['Status',l.status],['Current Stage',l.current_stage]
      ])+
      (loans.length?`<div class="live-card"><h3>Application History</h3><div class="table-scroll"><table><thead><tr><th>Loan</th><th>Requested</th><th>Eligible</th><th>Score</th><th>Approval</th><th>Status</th></tr></thead><tbody>${loans.map(x=>`<tr><td>${esc(x.id)}</td><td>${esc(money(x.requested_amount))}</td><td>${esc(money(x.eligible_amount))}</td><td>${esc(val(x.scorecard_score))}</td><td>${x.scorecard_approval_percent==null?'—':esc(x.scorecard_approval_percent+'%')}</td><td>${esc(val(x.status))}</td></tr>`).join('')}</tbody></table></div></div>`:'');
      addEligibilityMicroDetails(c,l,k,risk);
    }
    view.insertAdjacentHTML("beforeend", referenceDetails(data,key));
  }

  function buildSelector(options){
    let select=document.getElementById('applicationSelector');
    if(!select){
      const host=document.querySelector('.application-context');
      select=document.createElement('select');
      select.id='applicationSelector';
      select.setAttribute('aria-label','Select application');
      select.style.cssText='margin-left:auto;min-width:260px;max-width:360px;padding:9px 12px;border:1px solid #d7e1ef;border-radius:8px;background:#fff;color:#173052;font-weight:600';
      host.appendChild(select);
      select.addEventListener('change',()=>loadSelected(select.value));
    }
    select.innerHTML=options.map(o=>`<option value="${esc(o.value)}">${esc(o.label)}</option>`).join('');
    if(selected && options.some(o=>o.value===selected)) select.value=selected;
  }

  async function loadSelected(key){
    if(!key)return;
    selected=key;
    view.innerHTML='<div class="live-empty">Loading application data…</div>';
    try{
      const [source,id]=key.split(':');
      if(source!=='live' && source!=='demo') throw new Error('Unknown application source.');
      data=await window.DirectCreditData.customer(Number(id),source==='demo'
        ? {source:'demo'}
        : {source:'live',strictLive:true});
      const c=data.customer||{};
      const isDemo=source==='demo';
      document.getElementById('contextCustomer').textContent=val(c.name,'Customer');
      document.getElementById('contextId').textContent=`${isDemo?'Demo Test':'Live'} • Customer ID ${val(c.id,id)} • ${val(c.customer_code,'No customer code')}`;
      document.getElementById('contextStatus').textContent=isDemo?'Demo test record':'Live database';
      render(document.querySelector('.application-tab.active')?.dataset.view||'profile');
    }catch(e){
      data=null;
      document.getElementById('contextStatus').textContent='Data unavailable';
      view.innerHTML=`<div class="live-empty">Unable to load this application. ${esc(e.message||'Please try again.')}</div>`;
    }
  }

  async function load(){
    view.innerHTML='<div class="live-empty">Loading application list…</div>';
    try{
      // Keep the 10 built-in demo records available for testing, while live
      // customer/application records remain the primary production source.
      const liveRows=window.DirectCreditData.liveLoans
        ? await window.DirectCreditData.liveLoans()
        : await window.DirectCreditData.loans();
      const live=Array.isArray(liveRows)?liveRows:[];
      const liveCustomers=[...new Map(live.filter(x=>x.customer_id!=null).map(x=>[String(x.customer_id),x])).values()];
      const liveOptions=liveCustomers.map(x=>({
        value:'live:'+x.customer_id,
        label:`LIVE • ${x.customer_name||'Customer '+x.customer_id}${x.business_name?' • '+x.business_name:''} • Application #${x.id||x.loan_id||'—'}`
      }));
      const demoCustomers=window.DirectCreditData.demoCustomers||[];
      const demoOptions=demoCustomers.map(x=>({
        value:'demo:'+x.id,
        label:`DEMO TEST • ${x.name}${x.business_name?' • '+x.business_name:''} • Application #${x.loan?.id||'—'}`
      }));
      const options=[...liveOptions,...demoOptions];
      if(!options.length){
        view.innerHTML='<div class="live-empty">No application records are available.</div>';
        return;
      }
      buildSelector(options);
      const requested=params.get('customer_id');
      const requestedSource=params.get('source');
      const requestedKey=requested && (requestedSource==='live' || requestedSource==='demo')
        ? requestedSource+':'+requested : '';
      selected=requestedKey && options.some(o=>o.value===requestedKey)
        ? requestedKey : options[0].value;
      document.getElementById('applicationSelector').value=selected;
      await loadSelected(selected);
    }catch(e){
      view.innerHTML=`<div class="live-empty">Application data could not be loaded. ${esc(e.message||'Please check the database/API connection and refresh.')}</div>`;
    }
  }

  document.querySelectorAll('.application-tab').forEach(b=>b.addEventListener('click',()=>{
    document.querySelectorAll('.application-tab').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    render(b.dataset.view);
  }));
  document.getElementById('refreshBtn')?.addEventListener('click',load);
  document.getElementById('exportBtn')?.addEventListener('click',()=>window.print());
  load();
})();