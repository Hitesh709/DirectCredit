document.addEventListener('DOMContentLoaded',async()=>{
 const id=new URLSearchParams(location.search).get('customer_id');
 const host=document.getElementById('live');
 const base=(window.DIRECTCREDIT_API_URL||localStorage.getItem('directcredit_api_url')||'/api').replace(/\/$/,'');
 const token=localStorage.getItem('directcredit_admin_token')||window.DIRECTCREDIT_ADMIN_TOKEN;
 const headers=token?{Accept:'application/json',Authorization:`Bearer ${token}`}:{Accept:'application/json'};
 const esc=v=>String(v??'Not available').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
 const val=(v,f='Not available')=>v===null||v===undefined||String(v).trim()===''?f:String(v);
 const card=(title,rows)=>`<section class="detail-card"><div class="card-title"><h3>${esc(title)}</h3></div><div class="field-grid">${rows.map(x=>`<div class="field"><small>${esc(x[0])}</small><strong>${esc(val(x[1]))}</strong></div>`).join('')}</div></section>`;
 const table=(title,headers,rows,empty='No records available')=>`<section class="detail-card table-card"><div class="card-title"><h3>${esc(title)}</h3><a href="#">View all</a></div><div class="table-scroll"><table><thead><tr>${headers.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.length?rows.map(r=>`<tr>${r.map(v=>`<td>${esc(val(v))}</td>`).join('')}</tr>`).join(''):`<tr><td colspan="${headers.length}">${esc(empty)}</td></tr>`}</tbody></table></div></section>`;
 if(!id||!/^[0-9]+$/.test(id)){host.innerHTML='<h2>No customer selected</h2>';return;}
 try{
  let d; const r=await fetch(base+'/admin/reports/customer/'+id+'/profile',{headers});
  if(!r.ok)throw Error(r.status); d=await r.json();
  const c=d.customer||{}, bank=d.bank_analysis||{}, comm=d.communication_history||d.communications||[], devices=d.devices||d.device_history||[], notes=d.contact_notes||d.notes||[];
  const mobile=c.mobile, alt=c.alternate_mobile||c.alternate_phone||c.secondary_mobile;
  const email=c.email, altEmail=c.alternate_email;
  const contactScore=c.contact_score;
  const commRows=Array.isArray(comm)?comm.slice(0,20).map(x=>[x.date||x.created_at,x.channel,x.to||x.recipient,x.purpose,x.status]):[];
  const deviceRows=Array.isArray(devices)?devices.slice(0,10).map(x=>[x.device||x.device_model,x.sim_status||x.sim,x.last_seen,x.status]):[];
  const noteRows=Array.isArray(notes)?notes.slice(0,10).map(x=>[x.note||x.text,x.created_by||x.author,x.created_at]):[];
  host.innerHTML=`
   <div class="customer-banner panel">
    <div class="customer-main"><div class="avatar">${esc(String(c.name||'CU').split(/\s+/).slice(0,2).map(x=>x[0]).join('').toUpperCase())}</div><div><h2>${esc(c.name||'Customer')}</h2><p>Customer ID ${esc(c.id)}</p><strong>${esc(c.customer_code||'No customer code')}</strong></div><mark>Active</mark></div>
    <div class="metric blue"><small>REGISTERED MOBILE</small><strong>${esc(val(mobile))}</strong><span>${mobile?'Verified':'Not available'}</span></div>
    <div class="metric purple"><small>ALTERNATE MOBILE</small><strong>${esc(val(alt))}</strong><span>${alt?'Verified':'Not recorded'}</span></div>
    <div class="metric orange"><small>REGISTERED EMAIL</small><strong>${esc(val(email))}</strong><span>${email?(c.email_verified?'Verified':'Pending'):'Not available'}</span></div>
    <div class="metric green"><small>CONTACT SCORE</small><strong>${esc(contactScore==null?'Not available':contactScore+' / 100')}</strong><span>${contactScore==null?'Not assessed':'Recorded score'}</span></div>
   </div>
   <div class="top-grid">
    ${card('REGISTERED CONTACT',[['Registered Mobile',mobile],['Mobile Verification',mobile?'Verified':'Not available'],['Primary / Alternate',mobile?'Primary mobile':'Not available'],['Registered Email',email],['Email Verification',email?(c.email_verified?'Verified':'Pending'):'Not available'],['Customer ID',c.id]])}
    ${card('ADDRESS DETAILS',[['Current Address',c.address],['Permanent Address',c.permanent_address],['City',c.current_city],['Residence Ownership',c.residence_ownership],['Residence Since',c.residence_since],['PIN / Postal Code',c.pincode||c.postal_code]])}
    ${card('CONTACT & ACCOUNT',[['Business Name',c.business_name],['Business Type',c.business_type],['Primary Bank',c.primary_bank],['KYC Status',c.kyc_status],['Preferred Channel',c.communication_preference||c.preferred_contact_channel],['Consent',c.communication_consent||'Not available']])}
   </div>
   <div class="two-grid">
    ${table('MOBILE NUMBERS',['Number','Type','Verified On','Status','Action'],[
      [mobile,'Primary',c.mobile_verified_at||'Not available',mobile?'Verified':'Not available','View'],
      [alt,'Alternate',c.alternate_mobile_verified_at||'Not available',alt?'Verified':'Not recorded',alt?'View':'—']
    ])}
    ${table('EMAIL ADDRESSES',['Email','Type','Verified On','Status','Action'],[
      [email,'Primary',c.email_verified_at||'Not available',email?(c.email_verified?'Verified':'Pending'):'Not available','View'],
      [altEmail,'Alternate',c.alternate_email_verified_at||'Not available',altEmail?'Verified':'Not recorded',altEmail?'View':'—']
    ])}
   </div>
   ${table('COMMUNICATION HISTORY',['Date & Time','Channel','To / Recipient','Purpose','Status'],commRows)}
   <div class="two-grid">
    ${card('DEVICE & SIM INFORMATION',[['Device',c.device_model||c.device],['SIM / SIM Status',c.sim_status],['SIM Type',c.sim_type],['Last Seen',c.device_last_seen||c.last_device_seen],['Device Risk Score',c.device_risk_score],['Mobile Stability',c.mobile_stability]])}
    ${card('CONTACT NOTES',[['Latest Note',notes[0]?.note||notes[0]?.text],['Added By',notes[0]?.created_by||notes[0]?.author],['Last Updated',notes[0]?.created_at],['Verification Note',c.contact_verification_note],['Operational Note',c.contact_operational_note]])}
   </div>
   ${deviceRows.length?table('DEVICE / SIM HISTORY',['Device','SIM','Last Seen','Status'],deviceRows):''}
   <div class="notice">Contact information shown here is sourced from the selected customer record. Use verified contact channels for servicing and keep communication auditable.</div>
  `;
 }catch(e){host.innerHTML='<h2>Contact data unavailable</h2><p>Unable to load the selected live customer record.</p>';}
});