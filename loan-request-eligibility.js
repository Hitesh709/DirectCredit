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
      if(source==='demo'){
        data=window.DirectCreditData.demoCustomer(Number(id));
      }else{
        data=await window.DirectCreditData.customer(Number(id),{source:'live'});
      }
      const c=data.customer||{};
      document.getElementById('contextCustomer').textContent=val(c.name,'Customer');
      document.getElementById('contextId').textContent=`${source==='demo'?'Demo':'Live'} • Customer ID ${val(c.id,id)} • ${val(c.customer_code,'No customer code')}`;
      document.getElementById('contextStatus').textContent=source==='demo'?'Demo customer':'Live database';
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
      const liveRows=await window.DirectCreditData.loans();
      const live=Array.isArray(liveRows)?liveRows:[];
      const liveCustomers=[...new Map(live.filter(x=>x.customer_id!=null).map(x=>[String(x.customer_id),x])).values()];
      const demo=(window.DirectCreditData.demoCustomers||[]).map(c=>({customer_id:c.id,customer_name:c.name,business_name:c.business_name,requested_amount:c.loan?.requested_amount,status:c.loan?.status}));
      const options=[
        ...demo.map(x=>({value:'demo:'+x.customer_id,label:`DEMO • ${x.customer_name} • ${x.business_name||'Customer '+x.customer_id}`})),
        ...liveCustomers.map(x=>({value:'live:'+x.customer_id,label:`LIVE • ${x.customer_name||'Customer '+x.customer_id}${x.business_name?' • '+x.business_name:''}`}))
      ];
      if(!options.length){
        view.innerHTML='<div class="live-empty">No demo or live applications are available.</div>';
        return;
      }
      buildSelector(options);
      const requested=params.get('customer_id');
      const requestedSource=params.get('source');
      selected=requested?(requestedSource==='live'?'live:':'demo:')+requested:options[0].value;
      document.getElementById('applicationSelector').value=selected;
      await loadSelected(selected);
    }catch(e){
      // Even if live pipeline is unavailable, demo applications remain usable.
      const demo=(window.DirectCreditData.demoCustomers||[]).map(c=>({value:'demo:'+c.id,label:`DEMO • ${c.name} • ${c.business_name}`}));
      buildSelector(demo);
      if(demo.length){selected=demo[0].value;document.getElementById('applicationSelector').value=selected;await loadSelected(selected);}
      else view.innerHTML='<div class="live-empty">Application data is unavailable.</div>';
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