const API=(window.DIRECTCREDIT_API_URL||'/api').replace(/\/$/,'');const TOKEN='directcredit_customer_token',CID='directcredit_customer_id';let data=null,app=null,wi=0;
const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));const money=v=>v==null||v===''||Number.isNaN(Number(v))?'—':'₹'+Number(v).toLocaleString('en-IN');const txt=(v,f='—')=>v==null||String(v).trim()===''?f:String(v);const stat=v=>txt(v).replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
async function api(path,opt={}){const h={Accept:'application/json',...(opt.headers||{})},t=sessionStorage.getItem(TOKEN);if(t)h.Authorization='Bearer '+t;const r=await fetch(API+path,{...opt,headers:h});const b=await r.json().catch(()=>null);if(!r.ok)throw Error(b?.detail||b?.message||('Request failed ('+r.status+')'));return b}
function msg(id,s,e=false){const x=document.getElementById(id);if(x){x.textContent=s||'';x.className='msg'+(e?' error':' success')}}
async function load(){const id=sessionStorage.getItem(CID);if(!id)throw Error('No customer session');data=await api('/services/api/v1/customers/'+encodeURIComponent(id)+'/360');render();await loadApps();await loadActive()}
function go(page){document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x.id===page));document.querySelectorAll('.nav').forEach(x=>x.classList.toggle('active',x.dataset.page===page));const names={dashboard:'Dashboard',application:'Applications',loans:'My Loans',repayments:'Repayments',documents:'Documents',profile:'My Profile',support:'Support'};document.getElementById('title').textContent=names[page]||'Customer';}
function render(){const c=data.customer||{},m=data.metrics||{},r=data.risk_score||{},loans=data.loans||[],reps=data.repayments||[],j=data.journey||[];document.getElementById('welcome').textContent='Welcome, '+txt(c.name,'Customer');document.getElementById('score').textContent=r.total_score??c.cibil_score??'—';document.getElementById('decision').textContent=stat(r.decision||r.risk_tier||'Not assessed');document.getElementById('kLoans').textContent=m.total_loans??loans.length;document.getElementById('kSanctioned').textContent=money(m.total_loan_amount);document.getElementById('kOutstanding').textContent=money(m.outstanding_amount);const next=reps.filter(x=>Number(x.due_amount||0)>Number(x.paid_amount||0)).sort((a,b)=>String(a.due_date).localeCompare(String(b.due_date)))[0];document.getElementById('kNext').textContent=next?money(Math.max(Number(next.due_amount||0)-Number(next.paid_amount||0),0)):'—';document.getElementById('kNextDate').textContent=next?'Due '+txt(next.due_date):'No upcoming EMI';document.getElementById('status').textContent='Connected';document.getElementById('mini').innerHTML='<div class="avatar">'+esc(String(c.name||'CU').split(/\s+/).slice(0,2).map(x=>x[0]).join('').toUpperCase())+'</div><div><b>'+esc(txt(c.name,'Customer'))+'</b><small>'+esc(txt(c.customer_code||c.id))+'</small></div>';renderJourney(j);renderLatest(loans);renderRepayments(reps);renderLoans(loans);renderProfile(c,r);renderBank(c,data);renderDocs(data.documents||[]);renderAppsInline();}
function renderJourney(rows){const h=document.getElementById('journey');if(!rows.length){h.innerHTML='<div class="notice">No application journey recorded yet.</div>';return}h.innerHTML=[...rows].sort((a,b)=>(a.step_number||0)-(b.step_number||0)).map((x,i)=>'<div class="journey-row '+(['completed','complete','done'].includes(String(x.status).toLowerCase())?'done':'')+'"><span class="journey-num">'+esc(x.step_number||i+1)+'</span><div><b>'+esc(txt(x.step_label||x.step_key))+'</b><small>'+esc(stat(x.status))+'</small></div></div>').join('')}
function renderLatest(ls){const x=ls[0],h=document.getElementById('latest');h.innerHTML=x?['Loan ID|'+x.id,'Product|'+x.product,'Sanctioned|'+money(x.sanctioned_amount),'Outstanding|'+money(x.outstanding_amount),'EMI|'+money(x.monthly_emi),'Status|'+stat(x.status)].map(v=>{const[a,b]=v.split('|');return '<div><span>'+esc(a)+'</span><b>'+esc(b)+'</b></div>'}).join(''):'<div class="notice">No loan records yet.</div>'}
function renderRepayments(rs){const p=rs.reduce((s,x)=>s+Number(x.paid_amount||0),0),u=rs.reduce((s,x)=>s+Math.max(Number(x.due_amount||0)-Number(x.paid_amount||0),0),0);document.getElementById('paid').textContent=money(p);document.getElementById('unpaid').textContent=money(u);const n=rs.filter(x=>Number(x.due_amount||0)>Number(x.paid_amount||0)).sort((a,b)=>String(a.due_date).localeCompare(String(b.due_date)))[0];document.getElementById('repNext').textContent=n?money(Math.max(Number(n.due_amount||0)-Number(n.paid_amount||0),0)):'—';document.getElementById('repNextDate').textContent=n?txt(n.due_date):'—';document.getElementById('repRows').innerHTML=rs.length?rs.map(x=>'<tr><td>'+esc(txt(x.due_date))+'</td><td>'+esc(txt(x.loan_id))+'</td><td>'+esc(txt(x.installment))+'</td><td>'+esc(money(x.due_amount))+'</td><td>'+esc(money(x.paid_amount))+'</td><td>'+esc(money(Math.max(Number(x.due_amount||0)-Number(x.paid_amount||0),0)))+'</td><td>'+esc(stat(x.status))+'</td><td>'+esc(txt(x.dpd))+'</td></tr>').join(''):'<tr><td colspan="8">No repayment records found.</td></tr>';document.getElementById('dashRepay').innerHTML=n?'<div class="detail-grid"><div><span>Due Date</span><b>'+esc(txt(n.due_date))+'</b></div><div><span>Amount</span><b>'+esc(money(Math.max(Number(n.due_amount||0)-Number(n.paid_amount||0),0)))+'</b></div><div><span>Loan</span><b>'+esc(txt(n.loan_id))+'</b></div><div><span>Status</span><b>'+esc(stat(n.status))+'</b></div></div>':'<div class="notice">No upcoming repayment recorded.</div>'}
function renderLoans(ls){const dis=ls.reduce((s,x)=>s+Number(x.disbursed_amount||0),0),out=ls.reduce((s,x)=>s+Number(x.outstanding_amount||0),0);document.getElementById('loanCount').textContent=ls.length;document.getElementById('loanDisbursed').textContent=money(dis);document.getElementById('loanOutstanding').textContent=money(out);document.getElementById('loanRows').innerHTML=ls.length?ls.map(x=>'<tr><td>'+esc(txt(x.id))+'</td><td>'+esc(txt(x.product))+'</td><td>'+esc(money(x.requested_amount))+'</td><td>'+esc(money(x.sanctioned_amount))+'</td><td>'+esc(money(x.disbursed_amount))+'</td><td>'+esc(money(x.outstanding_amount))+'</td><td>'+esc(money(x.monthly_emi))+'</td><td>'+esc(stat(x.status))+'</td><td>'+esc(stat(x.current_stage))+'</td></tr>').join(''):'<tr><td colspan="9">No loan records found.</td></tr>'}
function renderProfile(c,r){
 const rows=[
  ['Customer ID',c.customer_code||c.id],['Customer Code',c.customer_code],['Name',c.name],['Mobile',c.mobile],
  ['Email',c.email],['Date of Birth',c.date_of_birth],['Gender',c.gender],['Marital Status',c.marital_status],
  ['PAN',c.pan],['Aadhaar (Masked)',c.aadhaar_masked],['Customer Type',c.customer_type],['Occupation',c.occupation],
  ['Business',c.business_name],['Business Type',c.business_type],['Monthly Income',money(c.monthly_income)],
  ['Work Experience',c.work_experience_years==null?'—':c.work_experience_years+' years'],
  ['Years in Business',c.years_in_business==null?'—':c.years_in_business+' years'],['Dependents',c.dependents],
  ['Address',c.address],['Permanent Address',c.permanent_address],['City',c.current_city],
  ['Residence Ownership',c.residence_ownership],['Residence Since',c.residence_since],
  ['Primary Bank',c.primary_bank],['Average Bank Balance',money(c.average_bank_balance)],
  ['Existing EMI',money(c.existing_emi)],['KYC Status',c.kyc_status],['Email Verification',c.email_verified],
  ['Selfie Status',c.selfie_status],['Ownership Proof',c.ownership_proof_status]
 ];
 document.getElementById('profile').innerHTML=rows.map(x=>'<div><span>'+esc(x[0])+'</span><b>'+esc(txt(x[1]))+'</b></div>').join('');
 const contacts=data.contacts||[],addresses=data.addresses||[],businesses=data.businesses||[],kyc=data.kyc||{};
 document.getElementById('risk').innerHTML=[
  ['DirectCredit Score',r.total_score],['Max Score',r.max_score],['Decision',r.decision],
  ['Approval',r.approval_percent==null?'—':r.approval_percent+'%'],['Risk Tier',r.risk_tier],
  ['CIBIL',r.credit_score],['FOIR',r.foir==null?'—':r.foir+'%'],['Existing EMI',money(r.existing_emi)],
  ['KYC Record',kyc.status],['PAN Verification',kyc.pan_status],['Identity Verification',kyc.identity_status],
  ['Address Verification',kyc.address_status],['Business Verification',kyc.business_status],
  ['Registered Contacts',contacts.length],['Saved Addresses',addresses.length],['Saved Businesses',businesses.length]
 ].map(x=>'<div><span>'+esc(x[0])+'</span><b>'+esc(txt(x[1]))+'</b></div>').join('');
}
function renderBank(c,d){
 const b=d.bank_analysis||{},k=d.kyc_employment||{},accounts=d.bank_accounts||[],businesses=d.businesses||[],addresses=d.addresses||[];
 const rows=[
  ['Bank',c.primary_bank],['Average Balance',money(b.average_eod_balance||c.average_bank_balance)],
  ['Monthly Credit',money(b.average_monthly_credit)],['Monthly Debit',money(b.average_monthly_debit)],
  ['Total Transactions',b.total_transactions],['Credit Transactions',b.credit_transactions],['Debit Transactions',b.debit_transactions],
  ['Negative Balance Events',b.negative_balance_count],['Last Balance',money(b.last_balance)],
  ['Net Cash Flow',b.net_cash_flow==null?'—':money(b.net_cash_flow)],['KYC',k.kyc_status||c.kyc_status],
  ['Business Vintage',k.years_in_business==null?'—':k.years_in_business+' years'],
  ['Residence',k.residence_ownership||c.residence_ownership],['Ownership Proof',k.ownership_proof_status||c.ownership_proof_status],
  ['Bank Accounts',accounts.length],['Businesses',businesses.length],['Addresses',addresses.length]
 ];
 document.getElementById('bankBusiness').innerHTML=rows.map(x=>'<div><span>'+esc(x[0])+'</span><b>'+esc(txt(x[1]))+'</b></div>').join('');
 document.getElementById('supportRef').innerHTML=[
  ['Customer ID',c.customer_code||c.id],['Mobile',c.mobile],['Email',c.email],['Latest Loan',d.loans?.[0]?.id],
  ['Bank Account',accounts[0]?.account_number_masked],['IFSC',accounts[0]?.ifsc],['KYC',k.kyc_status||c.kyc_status]
 ].map(x=>'<div><span>'+esc(x[0])+'</span><b>'+esc(txt(x[1]))+'</b></div>').join('');
}function renderDocs(ds){document.getElementById('docs').innerHTML=ds.length?ds.map(x=>'<div class="doc"><b>'+esc(stat(x.document_type))+'</b><small>Loan: '+esc(txt(x.loan_id))+'</small><p>'+esc(stat(x.verification_status||'Recorded'))+'</p></div>').join(''):'<div class="panel notice">No document records found.</div>'}
function renderAppsInline(){const rows=JSON.parse(sessionStorage.getItem('dc_apps_cache')||'[]');const host=document.getElementById('apps');if(!rows.length){host.innerHTML='<div class="notice">No loan applications yet.</div>';return}host.innerHTML=rows.map(x=>'<div class="detail-grid" style="margin-bottom:8px"><div><span>Application</span><b>#'+esc(x.loan_id)+'</b></div><div><span>Product</span><b>'+esc(txt(x.product))+'</b></div><div><span>Requested</span><b>'+esc(money(x.requested_amount))+'</b></div><div><span>Status</span><b>'+esc(stat(x.status))+'</b></div></div>').join('')}
async function loadApps(){const id=sessionStorage.getItem(CID);try{const rows=await api('/services/loan-request/'+encodeURIComponent(id));sessionStorage.setItem('dc_apps_cache',JSON.stringify(rows));renderAppsInline()}catch(e){document.getElementById('apps').innerHTML='<div class="notice">Application data could not be loaded.</div>'}}
async function loadActive(){const id=sessionStorage.getItem(CID);try{const x=await api('/services/loan-request/'+encodeURIComponent(id)+'/active');app=x.application||null;if(app)openWizard(app)}catch(e){}}
const steps=[
 ['MOBILE_OTP','Mobile Number OTP','Verify your registered mobile number with OTP.'],
 ['PAN_GST','PAN & GST Verification','Enter PAN and, where applicable, verify GST details through the configured provider.'],
 ['AADHAAR_SELFIE','Aadhaar & Selfie','Complete Aadhaar verification by manual document upload or DigiLocker, then submit selfie.'],
 ['BANK_AA','Bank Account Aggregator','Give consent and connect your bank data through Account Aggregator.'],
 ['CIBIL_PAYMENT','CIBIL Payment','Review the bureau-check charge and continue to bureau verification.'],
 ['BUREAU','Bureau Check','CIBIL / CRIF check. Processing continues only after an approved bureau result.'],
 ['BASIC','Basic Details','Confirm auto-filled identity details and complete the remaining personal information.'],
 ['ADDRESS','Permanent & Current Address','Confirm permanent address and complete current address and family-member details.'],
 ['BUSINESS','Business Details','Complete business type, ownership, stability, stock, machinery and trade references.'],
 ['DOCUMENTS','Upload Documents','Upload additional bank, GST/business bills, business board and other business photographs.'],
 ['SUBMIT','Submit','Review and submit the completed application.'],
 ['ELIGIBILITY','Auto Eligibility Check','DirectCredit automatically evaluates eligibility and displays the decision.']
];

const wizardData={};
async function saveJourneyStep(key,label,details,status='completed'){
 const id=sessionStorage.getItem(CID);
 if(!id)return;
 try{
  await api('/services/customers/'+id+'/journey',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({loan:{id:app?.loan_id},steps:[{key,step_number:steps.findIndex(x=>x[0]===key)+1,label,status,details:details||{}}]})
  });
 }catch(e){console.warn('Journey save failed',e.message)}
}
async function providerRequest(provider,payload={}){
 const id=sessionStorage.getItem(CID);
 return api('/api/v1/providers/'+encodeURIComponent(id)+'/'+encodeURIComponent(provider)+'/request',{
  method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({payload,idempotency_key:'PORTAL-'+id+'-'+provider+'-'+Date.now()})
 });
}
async function recordConsent(provider,purpose){
 const id=sessionStorage.getItem(CID);
 return api('/api/v1/providers/'+encodeURIComponent(id)+'/consent',{
  method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({provider,purpose,accepted:true,consent_version:'CUSTOMER-PORTAL-1.0'})
 });
}
function openWizard(x){
 app=x;
 const stageMap={PAN:1,AADHAAR:2,PERSONAL:7,ADDRESS:8,BUSINESS:9,BANKING:9,DOCUMENTS:10,REVIEW:11,ASSESSMENT:12};
 const current=String(x.current_stage||'PAN').toUpperCase();
 wi=Math.max(0,(stageMap[current]||1)-1);
 document.getElementById('applyStart').classList.add('hidden');
 document.getElementById('wizard').classList.remove('hidden');
 document.getElementById('wRef').textContent='#'+x.loan_id+' · '+money(x.requested_amount)+' · '+x.tenure_months+' months';
 drawWizard();
}

function field(label,id,type='text',value='',extra=''){
 return '<label>'+esc(label)+'<input id="'+id+'" type="'+type+'" value="'+esc(value??'')+'" '+extra+'></label>';
}
function selectField(label,id,options,value=''){
 return '<label>'+esc(label)+'<select id="'+id+'"><option value="">Select</option>'+options.map(x=>'<option '+(String(value)===String(x)?'selected':'')+'>'+esc(x)+'</option>').join('')+'</select></label>';
}
function fileField(label,id,multiple=false){
 return '<label class="upload-field">'+esc(label)+'<input id="'+id+'" type="file" '+(multiple?'multiple':'')+' accept="image/*,.pdf,.jpg,.jpeg,.png"></label>';
}
function drawWizard(){
 const s=steps[wi];
 document.getElementById('wTitle').textContent=s[1];
 document.getElementById('wDesc').textContent=s[2];
 document.getElementById('wProgress').innerHTML=steps.map((x,i)=>'<div class="wstep '+(i<wi?'done ':'')+(i===wi?'current':'')+'"><b>'+(i+1)+'. '+esc(x[1])+'</b></div>').join('');
 const c=data?.customer||{}, b=data?.business_details||{}, bank=data?.bank_accounts?.[0]||{};
 let h='';
 if(wi===0){
  h='<div class="verification-card"><div class="verification-badge">OTP</div><div><b>Mobile number</b><p>'+esc(txt(c.mobile))+'</p></div><span class="pill blue">OTP required</span></div><div class="form-grid">'+field('Enter OTP','wOtp','text','','inputmode="numeric" maxlength="6" placeholder="6-digit OTP"')+'</div><div class="notice">SMS OTP delivery requires the configured OTP provider. This screen does not bypass OTP verification.</div>';
 }else if(wi===1){
  h='<div class="form-grid">'+field('PAN Number','wPan','text',c.pan||'','maxlength="10" placeholder="ABCDE1234F"')+field('GST Number','wGst','text',b.gstin||'','maxlength="15" placeholder="15-digit GSTIN"')+'</div><div id="panGstResult" class="verification-result"></div>';
 }else if(wi===2){
  h='<div class="form-grid">'+selectField('Aadhaar Verification Method','wAadhaarMethod',['Manual Upload','DigiLocker'])+fileField('Aadhaar Document','wAadhaarFile')+fileField('Selfie','wSelfieFile')+'</div><div id="aadhaarResult" class="verification-result"></div>';
 }else if(wi===3){
  h='<div class="consent-card"><h3>Bank Account Aggregator</h3><p>Connect your bank data only after giving explicit consent for credit assessment.</p><label><input id="wAAConsent" type="checkbox"> I consent to Account Aggregator data access for credit assessment.</label><button class="outline" type="button" id="wAAConnect">Connect Bank Accounts</button></div><div id="aaResult" class="verification-result"></div>';
 }else if(wi===4){
  h='<div class="payment-card"><h3>CIBIL payment</h3><p>The bureau-check payment step is shown here. Payment collection requires a configured payment provider.</p><div class="detail-grid"><div><span>Purpose</span><b>CIBIL / Bureau Check</b></div><div><span>Status</span><b id="cibilPaymentStatus">Pending</b></div></div><label><input id="wCibilConsent" type="checkbox"> I authorize the bureau-check charge and want to continue.</label></div>';
 }else if(wi===5){
  h='<div class="bureau-card"><h3>CIBIL / CRIF Bureau Check</h3><p>The configured bureau provider will return the bureau result. Processing continues only when the provider returns an approved result.</p><div class="form-grid">'+selectField('Preferred Bureau','wBureau',['CIBIL','CRIF'])+field('Bureau Reference','wBureauRef','text','','placeholder="Optional provider reference"')+'</div><div id="bureauResult" class="verification-result"></div>';
 }else if(wi===6){
  h='<div class="form-grid">'+field('Full Name','wFullName','text',c.name||'','readonly')+selectField('Gender','wGender',['Male','Female','Other'],c.gender)+field('Date of Birth','wDob','date',c.date_of_birth||'','readonly')+field('Father / Spouse Name','wFatherSpouse')+field('Education','wEducation')+field('Caste','wCaste')+selectField('Marital Status','wMarital',['Single','Married','Other'],c.marital_status)+field('Email ID','wEmail','email',c.email||'')+'</div>';
 }else if(wi===7){
  const same=String(c.address||'')===String(c.permanent_address||'')&&c.address;
  h='<div class="form-grid">'+field('Permanent Address','wPermanent', 'text',c.permanent_address||'')+field('PIN','wPin','','','inputmode="numeric" maxlength="6"')+field('City','wCity','text',c.current_city||'')+field('State','wState')+selectField('Residence Type','wResidence',['Owned','Rented'],c.residence_ownership)+field('Residence Since','wResidenceSince','text',c.residence_since||'')+'</div><label class="check-line"><input id="wSameAddress" type="checkbox" '+(same?'checked':'')+'> Current address is same as permanent address</label><div class="form-grid">'+field('Current Address','wCurrentAddress','text',same?(c.permanent_address||''):c.address||'')+'</div><h3>Family Members</h3><div id="familyRows" class="repeat-list"></div><button class="outline small" type="button" id="addFamily">+ Add Family Member</button>';
 }else if(wi===8){
  h='<div class="form-grid">'+selectField('Business Type','wBusinessType',['Manufacturing','Retail','Wholesale','Service','Other'],b.business_type||c.business_type)+field('Other Business Type','wOtherBusiness')+field('Name of Business','wBusinessName','text',b.legal_name||c.business_name||'')+field('Business Address','wBusinessAddress')+field('Business PIN','wBusinessPin','','','inputmode="numeric" maxlength="6"')+field('Business Stability / Vintage','wBusinessStability','number',b.business_vintage_years??c.years_in_business||'')+selectField('Business Ownership','wBusinessOwnership',['Own','Rented'],b.ownership_type)+field('Machinery Value','wMachinery','number','','min="0"')+field('Total Stock Value','wStock','number','','min="0"')+'</div><h3>Trade Reference</h3><div class="form-grid">'+field('Reference Name','wTradeName')+field('Reference Number','wTradeNumber','tel')+field('Firm Name','wTradeFirm')+'</div>';
 }else if(wi===9){
  h='<div class="upload-grid">'+fileField('Additional Bank Account','wDocBank',true)+fileField('GST / Business Sale-Purchase Bills','wDocBills',true)+fileField('Business Board Photo','wDocBoard')+fileField('Other Business Photos','wDocOther',true)+'</div><div class="notice">Files are registered against the application. Binary storage/upload requires the configured document storage provider.</div><div id="docResult" class="verification-result"></div>';
 }else if(wi===10){
  h='<div class="review-grid"><div><h3>Review before submission</h3><p>Confirm that the information and documents provided are accurate and belong to you.</p><label><input id="wConfirm" type="checkbox"> I confirm the application details.</label></div><div class="notice">Submitting moves the application to automated eligibility assessment.</div></div>';
 }else{
  h='<div class="eligibility-card"><div class="verification-badge">AUTO</div><div><h3>Automatic Eligibility Check</h3><p>DirectCredit will evaluate the application using the available customer, banking, bureau and business data.</p></div></div><div id="eligibilityResult" class="eligibility-result"></div>';
 }
 document.getElementById('wBody').innerHTML=h;
 if(wi===7)setupFamilyRows();
 if(wi===3)document.getElementById('wAAConnect')?.addEventListener('click',connectAA);
}

function setupFamilyRows(){
 const host=document.getElementById('familyRows'); if(!host)return;
 const add=()=>{const n=host.children.length+1;const row=document.createElement('div');row.className='repeat-row';row.innerHTML=field('Name','famName'+n)+field('Relation','famRelation'+n)+field('Mobile','famMobile'+n,'tel')+field('Income','famIncome'+n,'number','','min="0"')+'<button class="link remove-family" type="button">Remove</button>';host.appendChild(row)};
 document.getElementById('addFamily')?.addEventListener('click',add);add();
 document.getElementById('wSameAddress')?.addEventListener('change',e=>{const x=document.getElementById('wCurrentAddress');if(e.target.checked){x.value=document.getElementById('wPermanent').value;x.readOnly=true}else{x.readOnly=false}});
}

async function connectAA(){
 try{
  const consent=document.getElementById('wAAConsent');
  if(!consent?.checked)throw Error('Please provide Account Aggregator consent first.');
  await recordConsent('account_aggregator','credit_assessment');
  const result=await providerRequest('account_aggregator',{purpose:'credit_assessment'});
  document.getElementById('aaResult').innerHTML='<div class="notice">Account Aggregator status: <b>'+esc(result.status)+'</b></div>';
  wizardData.BANK_AA=result;
 }catch(e){document.getElementById('aaResult').innerHTML='<div class="notice error">Account Aggregator could not be connected: '+esc(e.message)+'</div>'}
}

async function nextWizard(){
 const id=sessionStorage.getItem(CID),lid=app?.loan_id;
 if(!id||!lid)return;
 try{
  const key=steps[wi][0];
  if(wi===0){
   const otp=(document.getElementById('wOtp')?.value||'').trim();
   if(!/^\\d{6}$/.test(otp))throw Error('Enter the 6-digit mobile OTP.');
   await saveJourneyStep(key,steps[wi][1],{mobile:custMobile(),'otp_verified':false},'pending');
   throw Error('OTP verification service is not configured yet. Configure the SMS/OTP provider before production use.');
  }else if(wi===1){
   const pan=(document.getElementById('wPan').value||'').trim().toUpperCase();
   const gst=(document.getElementById('wGst').value||'').trim().toUpperCase();
   if(!/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(pan))throw Error('Enter a valid PAN.');
   const pv=await api('/services/pan/validate?pan='+encodeURIComponent(pan),{method:'POST'});
   if(!pv.valid_format)throw Error('PAN format validation failed.');
   await api('/services/loan-request/'+id+'/'+lid+'/kyc',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({pan})});
   let gv=null;
   if(gst){gv=await providerRequest('gst',{pan,gstin:gst});if(gv.status==='SUCCESS'&&gv.data?.gstin&&String(gv.data.gstin).toUpperCase()!==gst)throw Error('GST verification response did not match the submitted GST number.');}
   wizardData.PAN_GST={pan_status:pv.verification_status,gst_status:gv?.status||'NOT_PROVIDED'};
   await saveJourneyStep(key,steps[wi][1],wizardData.PAN_GST);
   await stage('AADHAAR');
  }else if(wi===2){
   const method=document.getElementById('wAadhaarMethod').value;
   const af=document.getElementById('wAadhaarFile').files[0],sf=document.getElementById('wSelfieFile').files[0];
   if(!method||!af||!sf)throw Error('Select Aadhaar method and provide Aadhaar document and selfie.');
   const docs=[['AADHAAR',af],['SELFIE',sf]];
   for(const [type,file] of docs)await registerDoc(type,file);
   await saveJourneyStep(key,steps[wi][1],{method,aadhaar_file:af.name,selfie_file:sf.name});
   await stage('PERSONAL');
  }else if(wi===3){
   const result=wizardData.BANK_AA;
   if(!result||result.status!=='SUCCESS')throw Error('Connect Account Aggregator successfully before continuing.');
   await saveJourneyStep(key,steps[wi][1],{provider_status:result.status,request_id:result.request_id});
   await stage('BANKING');
  }else if(wi===4){
   if(!document.getElementById('wCibilConsent').checked)throw Error('Authorize the bureau-check payment step to continue.');
   await saveJourneyStep(key,steps[wi][1],{payment_status:'authorized',provider_payment:'not_configured'});
  }else if(wi===5){
   const bureau=document.getElementById('wBureau').value;
   if(!bureau)throw Error('Select CIBIL or CRIF.');
   const result=await providerRequest('bureau',{bureau,loan_id:lid});
   wizardData.BUREAU=result;
   document.getElementById('bureauResult').innerHTML='<div class="notice">Bureau provider status: <b>'+esc(result.status)+'</b></div>';
   if(result.status!=='SUCCESS')throw Error('Bureau check did not return an approved provider result. Current status: '+result.status);
   const bureauData=result.data||{};
   const score=Number(bureauData.score);
   const approved=Number.isFinite(score)?score>=650:String(bureauData.decision||bureauData.status||'').toUpperCase()==='APPROVED';
   if(!approved)throw Error('Bureau result is not approved. Processing stops at this step.');
   await saveJourneyStep(key,steps[wi][1],{bureau,status:result.status,score:Number.isFinite(score)?score:null});
  }else if(wi===6){
   const p={name:document.getElementById('wFullName').value,gender:document.getElementById('wGender').value,date_of_birth:document.getElementById('wDob').value,marital_status:document.getElementById('wMarital').value,email:document.getElementById('wEmail').value};
   const father=document.getElementById('wFatherSpouse').value,education=document.getElementById('wEducation').value,caste=document.getElementById('wCaste').value;
   if(!p.name||!p.gender||!p.date_of_birth||!p.marital_status||!p.email||!father||!education||!caste)throw Error('Complete all Basic Details.');
   await api('/services/customer-profile/'+id+'/personal',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
   await saveJourneyStep(key,steps[wi][1],{father_spouse_name:father,education,caste,email:p.email});
   await stage('ADDRESS');
  }else if(wi===7){
   const p={permanent_address:document.getElementById('wPermanent').value,current_city:document.getElementById('wCity').value,address:document.getElementById('wCurrentAddress').value,residence_ownership:document.getElementById('wResidence').value,residence_since:document.getElementById('wResidenceSince').value};
   if(!Object.values(p).every(Boolean))throw Error('Complete all address and residence fields.');
   const family=[...document.querySelectorAll('.repeat-row')].map(row=>({name:row.querySelector('[id^="famName"]')?.value,relation:row.querySelector('[id^="famRelation"]')?.value,mobile:row.querySelector('[id^="famMobile"]')?.value,income:Number(row.querySelector('[id^="famIncome"]')?.value||0)})).filter(x=>x.name||x.mobile);
   await api('/services/customer-profile/'+id+'/address-residence',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
   await saveJourneyStep(key,steps[wi][1],{...p,pin:document.getElementById('wPin').value,state:document.getElementById('wState').value,family_members:family});
   await stage('BUSINESS');
  }else if(wi===8){
   let type=document.getElementById('wBusinessType').value;
   if(type==='Other')type=document.getElementById('wOtherBusiness').value.trim();
   const p={customer_type:'Individual',business_name:document.getElementById('wBusinessName').value,business_type:type,monthly_income:Number(document.getElementById('wIncome')?.value||0),years_in_business:Number(document.getElementById('wBusinessStability').value||0),primary_bank:data?.customer?.primary_bank||''};
   if(!p.business_name||!type)throw Error('Enter business name and business type.');
   await api('/services/customer-profile/'+id+'/employment-business',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
   const extra={business_address:document.getElementById('wBusinessAddress').value,business_pin:document.getElementById('wBusinessPin').value,business_stability_years:p.years_in_business,business_ownership:document.getElementById('wBusinessOwnership').value,machinery_value:Number(document.getElementById('wMachinery').value||0),total_stock_value:Number(document.getElementById('wStock').value||0),trade_reference:{name:document.getElementById('wTradeName').value,number:document.getElementById('wTradeNumber').value,firm_name:document.getElementById('wTradeFirm').value}};
   await saveJourneyStep(key,steps[wi][1],{...p,...extra});
   await stage('DOCUMENTS');
  }else if(wi===9){
   const groups=[['ADDITIONAL_BANK_ACCOUNT','wDocBank'],['GST_BUSINESS_BILLS','wDocBills'],['BUSINESS_BOARD_PHOTO','wDocBoard'],['OTHER_BUSINESS_PHOTO','wDocOther']];
   let count=0;for(const [type,idf] of groups){for(const file of [...(document.getElementById(idf)?.files||[])]){await registerDoc(type,file);count++}}
   if(!count)throw Error('Select at least one document to upload.');
   await saveJourneyStep(key,steps[wi][1],{document_count:count,documents:'registered'});
   await stage('REVIEW');
  }else if(wi===10){
   if(!document.getElementById('wConfirm').checked)throw Error('Please confirm the application details.');
   await saveJourneyStep(key,steps[wi][1],{confirmed:true});
   await stage('ASSESSMENT');
  }else{
   const result=await api('/api/v1/credit/'+id+'/assess',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({loan_id:lid})});
   wizardData.ELIGIBILITY=result;
   document.getElementById('eligibilityResult').innerHTML='<div class="eligibility-summary"><div><span>Decision</span><b>'+esc(stat(result.decision))+'</b></div><div><span>Score</span><b>'+esc(txt(result.score))+'</b></div><div><span>Eligible Amount</span><b>'+esc(money(result.eligible_amount))+'</b></div><div><span>Approval</span><b>'+esc(result.approval_percent==null?'—':result.approval_percent+'%')+'</b></div></div>';
   await saveJourneyStep(key,steps[wi][1],result,result.decision==='REJECT'?'rejected':'completed');
   msg('wMsg','Eligibility check completed.');
   document.getElementById('wNext').disabled=true;
   await load();
   return;
  }
  if(wi<steps.length-1){wi++;drawWizard()}else await load();
 }catch(e){msg('wMsg',e.message,true)}
}
function custMobile(){return data?.customer?.mobile||''}
async function registerDoc(type,file){
 const id=sessionStorage.getItem(CID),lid=app?.loan_id;
 return api('/api/services/documents/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
  customer_id:Number(id),loan_id:Number(lid),document_type:type,file_name:file.name,mime_type:file.type||'application/octet-stream',file_size:file.size||0,source:'customer_portal',required:true,verification_status:'pending'
 })});
}
async function stage(s){
 const id=sessionStorage.getItem(CID),lid=app.loan_id;
 await api('/services/loan-request/'+id+'/'+lid+'/stage',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage:s})});
 app.current_stage=s;
}
async function apply(){const id=sessionStorage.getItem(CID),amount=Number(document.getElementById('amount').value),tenure=Number(document.getElementById('tenure').value);if(app){openWizard(app);return}if(amount<5000||amount>15000||![3,6,9,12].includes(tenure)){msg('applyMsg','Enter a valid amount (₹5,000–₹15,000) and tenure.',true);return}try{const x=await api('/services/loan-request/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product:'Micro Business Loan',requested_amount:amount,tenure_months:tenure})});app={loan_id:x.loan_id,requested_amount:x.requested_amount,tenure_months:x.tenure_months,product:x.product,status:x.status,current_stage:x.current_stage};openWizard(app);await loadApps()}catch(e){msg('applyMsg',e.message,true)}}
async function login(){const mobile=document.getElementById('mobile').value.replace(/\D/g,'').slice(0,10);if(mobile.length!==10){msg('accessMsg','Enter a valid 10-digit mobile number.',true);return}try{let x;try{x=await api('/auth/customer-mobile-login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mobile})})}catch(e){x=await api('/services/api/auth/customer-mobile-login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mobile})})}sessionStorage.setItem(TOKEN,x.access_token);sessionStorage.setItem(CID,String(x.customer.id));document.getElementById('access').classList.add('hidden');document.getElementById('app').classList.remove('hidden');await load();go('dashboard')}catch(e){msg('accessMsg',e.message,true)}}
async function signup(){const name=document.getElementById('signupName').value.trim(),mobile=document.getElementById('signupMobile').value.replace(/\D/g,'').slice(0,10);if(name.length<2||mobile.length!==10){msg('accessMsg','Enter a valid name and 10-digit mobile.',true);return}try{const x=await api('/services/api/auth/customer-register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,mobile})});sessionStorage.setItem(TOKEN,x.access_token);sessionStorage.setItem(CID,String(x.customer.id));document.getElementById('access').classList.add('hidden');document.getElementById('app').classList.remove('hidden');await load();go('dashboard')}catch(e){msg('accessMsg',e.message,true)}}
function logout(){sessionStorage.removeItem(TOKEN);sessionStorage.removeItem(CID);location.reload()}
document.addEventListener('click',e=>{const n=e.target.closest('.nav');if(n)go(n.dataset.page);const g=e.target.closest('[data-go]');if(g)go(g.dataset.go)});
document.getElementById('login').onclick=login;document.getElementById('signupBtn').onclick=signup;document.getElementById('signupToggle').onclick=()=>document.getElementById('signup').classList.toggle('hidden');document.getElementById('logout').onclick=logout;document.getElementById('print').onclick=()=>window.print();document.getElementById('applyBtn').onclick=apply;document.getElementById('wNext').onclick=nextWizard;document.getElementById('wBack').onclick=()=>{if(wi>0){wi--;drawWizard()}};document.getElementById('refreshApps').onclick=loadApps;
(async()=>{const id=sessionStorage.getItem(CID),t=sessionStorage.getItem(TOKEN);if(id&&t)try{document.getElementById('access').classList.add('hidden');document.getElementById('app').classList.remove('hidden');await load()}catch(e){logout()}})();