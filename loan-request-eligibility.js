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
      const latest=l||{};
      const initials=String(c.name||'Customer').split(/\\s+/).map(x=>x[0]).join('').slice(0,2).toUpperCase();
      const status=String(latest.status||'Not assessed');
      const statusClass=status==='active'||status==='repaid'?'good':status==='overdue'?'bad':'pending';
      const totalLoans=Number(m.total_loans ?? loans.length ?? 0);
      const totalAmount=Number(m.total_loan_amount??loans.reduce((s,x)=>s+Number(x.sanctioned_amount||x.requested_amount||0),0));
      const outstanding=Number(m.outstanding_amount??0);
      const paid=Number(m.amount_paid??0);
      const score=risk.credit_score??c.cibil_score;
      const innerTabs=['overview','loans','repayments','documents','communication','alerts','activity'];
      const renderInner=(inner)=>{
        const safe=(v)=>val(v,'Not available');
        if(inner==='loans') return `<div class="cp-section"><div class="cp-section-head"><div><h3>Loans</h3><p>Customer loan portfolio and current exposure.</p></div></div><div class="cp-table-wrap"><table class="cp-table"><thead><tr><th>Loan ID</th><th>Product</th><th>Requested</th><th>Sanctioned</th><th>Outstanding</th><th>EMI</th><th>Tenure</th><th>Status</th></tr></thead><tbody>${loans.length?loans.map(x=>`<tr><td class="primary">${esc(x.id)}</td><td>${esc(x.product||'Not available')}</td><td>${esc(money(x.requested_amount))}</td><td>${esc(money(x.sanctioned_amount))}</td><td class="money">${esc(money(x.outstanding_amount))}</td><td>${esc(money(x.monthly_emi))}</td><td>${x.tenure_months?esc(x.tenure_months+' months'):'—'}</td><td><span class="cp-status cp-${esc(String(x.status||'unknown').toLowerCase())}">${esc(x.status)}</span></td></tr>`).join(''):'<tr><td colspan="8">No loan records available.</td></tr>'}</tbody></table></div></div>`;
        if(inner==='repayments'){
          const reps=Array.isArray(data.repayments)?data.repayments:Array.isArray(data.repayment_records)?data.repayment_records:[];
          return `<div class="cp-section"><div class="cp-section-head"><div><h3>Repayment History</h3><p>Payments and repayment obligations returned by the customer record.</p></div></div><div class="cp-table-wrap"><table class="cp-table"><thead><tr><th>Date</th><th>Loan</th><th>Due</th><th>Paid</th><th>Unpaid</th><th>Status</th><th>DPD</th></tr></thead><tbody>${reps.length?reps.map(x=>`<tr><td>${esc(x.due_date||x.paid_at||x.date)}</td><td class="primary">${esc(x.loan_id)}</td><td>${esc(money(x.due_amount))}</td><td class="money">${esc(money(x.paid_amount))}</td><td class="money">${esc(money(x.unpaid_amount))}</td><td>${esc(x.status)}</td><td>${esc(x.dpd??'—')}</td></tr>`).join(''):'<tr><td colspan="7">No repayment history is available in the returned customer record.</td></tr>'}</tbody></table></div></div>`;
        }
        if(inner==='documents'){
          const docs=Array.isArray(data.documents)?data.documents:[];
          return `<div class="cp-section"><div class="cp-section-head"><div><h3>Documents</h3><p>KYC and supporting documents available for this customer.</p></div></div><div class="cp-doc-grid">${docs.length?docs.map(x=>`<div class="cp-doc"><div class="cp-doc-icon">▣</div><div><strong>${esc(x.document_type||x.type||x.name)}</strong><small>${esc(x.status||'Uploaded')}</small></div></div>`).join(''):'<div class="cp-empty">No document records were returned for this customer.</div>'}</div></div>`;
        }
        const events=Array.isArray(data.events)?data.events:[];
        if(inner==='communication') return `<div class="cp-section"><div class="cp-section-head"><div><h3>Communication</h3><p>Customer communication activity from the source record.</p></div></div>${events.length?'<div class="cp-timeline">'+events.map(x=>`<div class="cp-event"><span></span><div><strong>${esc(x.event_type||x.type||x.channel||'Customer event')}</strong><small>${esc(x.created_at||x.event_at||x.date||'')}</small><p>${esc(x.description||x.purpose||x.message||'Recorded customer activity')}</p></div></div>`).join('')+'</div>':'<div class="cp-empty">No communication history is available in the returned customer record.</div>'}</div>`;
        if(inner==='alerts') return `<div class="cp-section"><div class="cp-section-head"><div><h3>Notes & Alerts</h3><p>Risk, verification and follow-up items available from the record.</p></div></div><div class="cp-alert-grid"><div class="cp-alert ${statusClass}"><strong>Loan status</strong><span>${esc(status)}</span><small>Latest application</small></div><div class="cp-alert"><strong>KYC status</strong><span>${esc(k.kyc_status||c.kyc_status)}</span><small>Verification state</small></div><div class="cp-alert"><strong>Ownership proof</strong><span>${esc(k.ownership_proof_status||c.ownership_proof_status)}</span><small>Document state</small></div></div></div>`;
        if(inner==='activity') return `<div class="cp-section"><div class="cp-section-head"><div><h3>Activity Log</h3><p>Recorded customer/application events.</p></div></div>${events.length?'<div class="cp-timeline">'+events.map(x=>`<div class="cp-event"><span></span><div><strong>${esc(x.event_type||x.type||'Activity')}</strong><small>${esc(x.created_at||x.event_at||x.date||'')}</small><p>${esc(x.description||x.purpose||'Recorded activity')}</p></div></div>`).join('')+'</div>':'<div class="cp-empty">No activity log records are available.</div>'}</div>`;
        return `
          <div class="cp-main-grid">
            <div class="cp-section cp-summary"><div class="cp-section-head"><div><h3>Customer Summary</h3><p>Core customer, employment and financial profile.</p></div></div>
              <div class="cp-field-grid">
                <div><small>Occupation</small><b>${esc(c.occupation)}</b></div><div><small>Business</small><b>${esc(c.business_name)}</b></div>
                <div><small>Monthly Income</small><b>${money(c.monthly_income)}</b></div><div><small>Work Experience</small><b>${c.work_experience_years!=null?esc(c.work_experience_years+' Years'):'Not available'}</b></div>
                <div><small>Years in Business</small><b>${c.years_in_business!=null?esc(c.years_in_business+' Years'):'Not available'}</b></div><div><small>Average Bank Balance</small><b>${money(c.average_bank_balance??bank.average_eod_balance)}</b></div>
                <div><small>Primary Bank</small><b>${esc(c.primary_bank)}</b></div><div><small>CIBIL Score</small><b class="score">${esc(score)}</b></div>
                <div><small>FOIR</small><b>${c.foir!=null?esc(c.foir+'%'):'Not available'}</b></div><div><small>Existing EMI</small><b>${money(c.existing_emi)}</b></div>
                <div><small>Dependents</small><b>${esc(c.dependents??'Not available')}</b></div><div><small>KYC Status</small><b>${esc(k.kyc_status||c.kyc_status)}</b></div>
              </div>
            </div>
            <div class="cp-section"><div class="cp-section-head"><div><h3>Latest Loan Overview</h3><p>Current application and repayment position.</p></div></div>
              <div class="cp-loan-list">
                <div><span>Loan Account</span><b>${esc(latest.id)}</b></div><div><span>Loan Product</span><b>${esc(latest.product)}</b></div>
                <div><span>Requested Amount</span><b>${money(latest.requested_amount)}</b></div><div><span>Sanctioned Amount</span><b>${money(latest.sanctioned_amount)}</b></div>
                <div><span>Disbursed Amount</span><b>${money(latest.disbursed_amount)}</b></div><div><span>Tenure</span><b>${latest.tenure_months?esc(latest.tenure_months+' Months'):'Not available'}</b></div>
                <div><span>Interest Rate</span><b>${latest.interest_rate!=null?esc(latest.interest_rate+'% P.A.'):'Not available'}</b></div><div><span>EMI Amount</span><b>${money(latest.monthly_emi)}</b></div>
                <div><span>Outstanding</span><b class="money">${money(latest.outstanding_amount)}</b></div><div><span>Loan Status</span><b><span class="cp-status cp-${esc(status.toLowerCase())}">${esc(status)}</span></b></div>
              </div>
            </div>
          </div>
          <div class="cp-overview-grid">
            <div class="cp-section cp-score-card"><div class="cp-section-head"><div><h3>Credit Score Gauge</h3><p>Current bureau score returned for this customer.</p></div></div><div class="cp-gauge"><div class="cp-gauge-arc"></div><strong>${esc(score??'—')}</strong><span>${esc(risk.risk_tier||'Not assessed')}</span><small>Credit / CIBIL Score</small></div></div>
            <div class="cp-section"><div class="cp-section-head"><div><h3>Latest Repayment Activity</h3><p>Most recent repayment records available.</p></div></div><div class="cp-mini-list">${(Array.isArray(data.repayments)?data.repayments:Array.isArray(data.repayment_records)?data.repayment_records:[]).slice(0,5).map(x=>`<div><span>${esc(x.paid_at||x.due_date||x.date||'—')}</span><b>${money(x.paid_amount)}</b><small>${esc(x.status||'Recorded')}</small></div>`).join('')||'<div class="cp-empty">No repayment history is available.</div>'}</div></div>
          </div>
          <div class="cp-section"><div class="cp-section-head"><div><h3>Active Loans</h3><p>Current customer loan exposure.</p></div></div><div class="cp-table-wrap"><table class="cp-table"><thead><tr><th>Loan Account</th><th>Product</th><th>Sanctioned</th><th>Outstanding</th><th>EMI</th><th>Next Due</th><th>Status</th></tr></thead><tbody>${loans.map(x=>`<tr><td class="primary">${esc(x.id)}</td><td>${esc(x.product)}</td><td>${esc(money(x.sanctioned_amount))}</td><td class="money">${esc(money(x.outstanding_amount))}</td><td>${esc(money(x.monthly_emi))}</td><td>${esc(x.next_due_date||'Not available')}</td><td><span class="cp-status cp-${esc(String(x.status||'').toLowerCase())}">${esc(x.status)}</span></td></tr>`).join('')}</tbody></table></div></div>
        `;
      };
      view.innerHTML=`
        <div class="cp-profile">
          <aside class="cp-sidebar">
            <div class="cp-avatar">${esc(initials)}</div><h2>${esc(c.name||'Customer')}</h2><span class="cp-active ${statusClass}">${esc(status)}</span>
            <div class="cp-id">Customer ID<br><strong>${esc(c.customer_code||c.id)}</strong></div>
            <div class="cp-side-grid"><div><small>Customer Since</small><b>${esc(c.created_at||c.customer_since||'Not available')}</b></div><div><small>Customer Type</small><b>${esc(c.customer_type)}</b></div></div>
            <h4>CONTACT INFORMATION</h4>
            <div class="cp-contact"><div>☎ <span>Mobile</span><b>${esc(c.mobile)}</b></div><div>✉ <span>Email</span><b>${esc(c.email)}</b></div><div>⌖ <span>Address</span><b>${esc(c.address)}</b></div><div>⌂ <span>Current City</span><b>${esc(c.current_city)}</b></div><div>▣ <span>Business</span><b>${esc(c.business_name)}</b></div><div>◉ <span>Business Type</span><b>${esc(c.business_type)}</b></div><div>◷ <span>Date of Birth</span><b>${esc(c.date_of_birth||c.dob)}</b></div><div>▤ <span>PAN</span><b>${esc(c.pan)}</b></div><div>▤ <span>Aadhaar</span><b>${esc(c.aadhaar_masked||c.aadhaar)}</b></div><div>♙ <span>Marital Status</span><b>${esc(c.marital_status)}</b></div></div>
          </aside>
          <section class="cp-content">
            <div class="cp-kpis">
              <div class="cp-kpi blue"><small>TOTAL LOANS</small><strong>${totalLoans}</strong><span>Customer portfolio</span></div>
              <div class="cp-kpi green"><small>TOTAL LOAN AMOUNT</small><strong>${money(totalAmount)}</strong><span>Sanctioned / requested</span></div>
              <div class="cp-kpi purple"><small>OUTSTANDING AMOUNT</small><strong>${money(outstanding)}</strong><span>Current exposure</span></div>
              <div class="cp-kpi orange"><small>AMOUNT PAID</small><strong>${money(paid)}</strong><span>Repayment position</span></div>
              <div class="cp-kpi navy"><small>CREDIT SCORE</small><strong>${esc(score)}</strong><span>${esc(risk.risk_tier||'Not assessed')}</span></div>
            </div>
            <div class="cp-inner-tabs">${innerTabs.map(t=>`<button class="cp-inner-tab ${t==='overview'?'active':''}" data-cp-view="${t}">${t==='overview'?'Overview':t==='loans'?'Loans':t==='repayments'?'Repayment History':t==='documents'?'Documents':t==='communication'?'Communication':t==='alerts'?'Notes & Alerts':'Activity Log'}</button>`).join('')}</div>
            <div id="cpInnerBody">${renderInner('overview')}</div>
          </section>
        </div>`;
      const cpBody=document.getElementById('cpInnerBody');
      view.querySelectorAll('.cp-inner-tab').forEach(btn=>btn.addEventListener('click',()=>{
        view.querySelectorAll('.cp-inner-tab').forEach(x=>x.classList.remove('active'));btn.classList.add('active');cpBody.innerHTML=renderInner(btn.dataset.cpView);
      }));
    } else if(key==='contact'){
      const contacts=Array.isArray(data.contacts)?data.contacts:[];
      const addresses=Array.isArray(data.addresses)?data.addresses:[];
      const events=Array.isArray(data.events)?data.events:[];
      const primaryMobile=read(data,['contact_details.registered_mobile','customer.mobile']);
      const altMobiles=contacts.filter(x=>String(x.contact_type||'').toLowerCase().includes('mobile')&&!x.is_primary).map(x=>x.contact_value||x.value).filter(Boolean);
      const emailRows=contacts.filter(x=>String(x.contact_type||'').toLowerCase().includes('email')).map(x=>x);
      const registeredEmail=read(data,['contact_details.registered_email','customer.email']);
      const primaryAddress=addresses.find(x=>x.is_primary)||addresses[0]||{};
      const device=read(data,['contact_details.device_sim'])||{};
      const fmtDate=v=>v?String(v).replace('T',' ').replace('Z',''): 'Not available';
      const contactStatus=v=>v===true?'Verified':v===false?'Not Verified':val(v,'Not available');
      const contactScore=read(data,['contact_details.contact_score','contact_score']);
      const contactCard=(title,body,cls='')=>`<div class="ct-card ${cls}"><div class="ct-card-title">${esc(title)}</div>${body}</div>`;
      const mobileRows=contacts.filter(x=>String(x.contact_type||'').toLowerCase().includes('mobile'));
      const commRows=events.slice().sort((a,b)=>String(b.created_at||b.event_at||'').localeCompare(String(a.created_at||a.event_at||''))).slice(0,6);
      const addrLine=primaryAddress.address_line||primaryAddress.address||c.address||'Not available';
      const city=primaryAddress.city||c.current_city||'Not available';
      const state=primaryAddress.state||c.current_state||'Not available';
      const pincode=primaryAddress.pincode||primaryAddress.zipcode||c.current_pincode||'Not available';
      view.innerHTML=`
        <div class="contact360">
          <div class="ct-hero">
            <div class="ct-customer">
              <div class="ct-avatar">${esc(String(c.name||'Customer').split(/\\s+/).map(x=>x[0]).join('').slice(0,2).toUpperCase())}</div>
              <div><h2>${esc(c.name||'Customer')} <span class="ct-pill good">${esc(l.status||'Active')}</span></h2>
              <small>Customer ID <b>${esc(c.customer_code||c.id)}</b></small>
              <small>Loan Account No. <b>${esc(l.id||'Not available')}</b></small></div>
            </div>
            <div class="ct-stat phone"><span>☎</span><small>REGISTERED MOBILE<br>NUMBER</small><strong>${esc(primaryMobile)}</strong><em>${contactStatus(c.mobile_verified)}</em></div>
            <div class="ct-stat alt"><span>◉</span><small>ALTERNATE MOBILE<br>NUMBER</small><strong>${esc(altMobiles[0]||'Not available')}</strong><em>${altMobiles.length?'Available':'Not available'}</em></div>
            <div class="ct-stat email"><span>✉</span><small>REGISTERED EMAIL ID</small><strong>${esc(registeredEmail)}</strong><em>${contactStatus(c.email_verified)}</em></div>
            <div class="ct-stat score"><span>✓</span><small>CONTACT SCORE</small><strong>${esc(contactScore??'Not available')}</strong><em>${contactScore!=null?'Verified contact quality':'Not assessed'}</em></div>
          </div>

          <div class="ct-grid-top">
            ${contactCard('REGISTERED MOBILE NUMBER',`
              <div class="ct-primary-line"><b>☎ ${esc(primaryMobile)}</b><span class="ct-pill good">${contactStatus(c.mobile_verified)}</span><span class="ct-pill blue">Primary</span></div>
              <div class="ct-detail-list">
                <div><span>Linked To</span><b>Customer • PAN • Loan Account</b></div>
                <div><span>Verified On</span><b>${fmtDate(read(data,['contact_details.mobile_verified_at','customer.mobile_verified_at']))}</b></div>
                <div><span>Verification Mode</span><b>${esc(read(data,['contact_details.mobile_verification_mode'])||'Not available')}</b></div>
                <div><span>Last OTP Sent</span><b>${fmtDate(read(data,['contact_details.last_otp_sent']))}</b></div>
                <div><span>Status</span><b>${contactStatus(c.mobile_verified)}</b></div>
              </div>`,'mobile-card')}

            ${contactCard('ALTERNATE MOBILE NUMBERS <span class="ct-add">+ Add Number</span>',`
              <div class="ct-mini-table"><div class="ct-th"><span>Mobile Number</span><span>Type</span><span>Verified On</span><span>Status</span></div>
              ${(mobileRows.length?mobileRows:altMobiles.map((x,i)=>({contact_value:x,contact_type:i?'Reference':'Alternate'}))).slice(0,5).map(x=>`<div class="ct-tr"><b>${esc(x.contact_value||x.value)}</b><span>${esc(x.contact_type||'Alternate')}</span><span>${fmtDate(x.verified_at||x.updated_at)}</span><span class="ct-pill ${x.verified?'good':'neutral'}">${x.verified?'Verified':'Not Verified'}</span></div>`).join('')||'<div class="ct-empty">No alternate mobile numbers are available.</div>'}</div>
              <div class="ct-note">ⓘ At least one verified mobile number is required for communication and OTP based verification.</div>`,'alt-card')}

            ${contactCard('EMAIL ADDRESS DETAILS <span class="ct-add">+ Add Email</span>',`
              <div class="ct-mini-table email-table"><div class="ct-th"><span>Email Address</span><span>Type</span><span>Verified On</span><span>Status</span></div>
              ${(emailRows.length?emailRows:[{contact_value:registeredEmail,contact_type:'Primary',verified:c.email_verified}]).slice(0,5).map(x=>`<div class="ct-tr"><b>${esc(x.contact_value||x.value)}</b><span>${esc(x.contact_type||'Email')}</span><span>${fmtDate(x.verified_at||x.updated_at)}</span><span class="ct-pill ${x.verified?'good':'neutral'}">${x.verified?'Verified':'Not Verified'}</span></div>`).join('')}</div>
              <div class="ct-note">ⓘ Important: All communication and documents will be sent to verified email addresses only.</div>`,'email-card')}
          </div>

          <div class="ct-grid-bottom">
            ${contactCard('COMMUNICATION HISTORY',`
              <div class="ct-comm-table"><div class="ct-th"><span>Date & Time</span><span>Channel</span><span>To</span><span>Purpose</span><span>Status</span></div>
              ${commRows.map(x=>`<div class="ct-tr"><span>${fmtDate(x.created_at||x.event_at)}</span><span>${esc(x.channel||x.event_type||'Activity')}</span><span>${esc(x.to||x.recipient||primaryMobile)}</span><span>${esc(x.purpose||x.description||x.event_type||'Customer activity')}</span><span class="ct-pill good">${esc(x.status||'Recorded')}</span></div>`).join('')||'<div class="ct-empty">No communication history is available.</div>'}</div>
              <div class="ct-link">View Full Communication Log →</div>`,'comm-card')}

            ${contactCard('ADDRESS <small>(as per KYC)</small>',`
              <div class="ct-address-main">${esc(addrLine)}, ${esc(city)}, ${esc(state)} - ${esc(pincode)}</div>
              <span class="ct-pill good">Verified</span>
              <div class="ct-detail-list">
                <div><span>Address Type</span><b>${esc(primaryAddress.address_type||'Current Address')}</b></div>
                <div><span>Verified On</span><b>${fmtDate(primaryAddress.verified_at||primaryAddress.updated_at)}</b></div>
                <div><span>Verified Via</span><b>${esc(primaryAddress.verified_via||'Not available')}</b></div>
                <div><span>Latitude</span><b>${esc(primaryAddress.latitude||'Not available')}</b></div>
                <div><span>Longitude</span><b>${esc(primaryAddress.longitude||'Not available')}</b></div>
              </div><div class="ct-link">View on Map ⌖</div>`,'address-card')}

            ${contactCard('DEVICE & SIM INFORMATION <small>(Latest)</small>',`
              <div class="ct-detail-list device-list">
                <div><span>Device</span><b>${esc(device.device||device.device_name||'Not available')}</b></div>
                <div><span>SIM Operator</span><b>${esc(device.sim_operator||device.operator||'Not available')}</b></div>
                <div><span>SIM Type</span><b>${esc(device.sim_type||'Not available')}</b></div>
                <div><span>Last Used</span><b>${fmtDate(device.last_used)}</b></div>
              </div>
              <div class="ct-risk-box"><span>◆</span><div><small>Device Risk Score</small><strong>${esc(device.risk_status||device.status||'Not available')}</strong></div></div>`,'device-card')}

            ${contactCard('CONTACT NOTES <span class="ct-add">+ Add Note</span>',`
              <div class="ct-note-box"><b>ⓘ Contact notes</b><p>${esc(read(data,['contact_details.notes','contact_notes','notes'])||'No contact notes are available in the customer record.')}</p><small>Source record</small></div>`,'notes-card')}
          </div>
        </div>`;
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
    if(key!=="contact") view.insertAdjacentHTML("beforeend", referenceDetails(data,key));
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
      let liveRows=[];
      try {
        liveRows=window.DirectCreditData.liveLoans
          ? await window.DirectCreditData.liveLoans()
          : await window.DirectCreditData.loans();
      } catch(_) {
        // A protected live endpoint may return 401; demo applications must remain testable.
        liveRows=[];
      }
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
  load();
})();