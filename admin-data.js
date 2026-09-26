const DEMO_CUSTOMERS = Array.from({length:10}, (_,i) => {
  const id = i + 1;
  const names = ['Aarav Shah','Priya Patel','Rohan Mehta','Neha Desai','Vikram Joshi','Kavya Shah','Dhruv Patel','Anjali Mehta','Rajesh Desai','Pooja Joshi'];
  const businesses = ['Shah Traders','Patel Foods','Mehta Garments','Desai Stationery','Joshi Electricals','Shah Home Needs','Patel Auto Parts','Mehta Boutique','Desai Hardware','Joshi General Store'];
  const banks = ['HDFC Bank','ICICI Bank','Axis Bank','SBI','Kotak Mahindra Bank'];
  const amounts = [5000,7500,10000,12500,15000,10000,7500,12500,15000,10000];
  const statuses = ['active','active','overdue','repaid','pending','active','overdue','active','repaid','pending'];
  const amount = amounts[i];
  const status = statuses[i];
  const outstanding = status === 'repaid' ? 0 : status === 'overdue' ? Math.round(amount*0.62) : status === 'pending' ? 0 : Math.round(amount*0.72);
  return {
    id, customer_code:`DEMO-CUST-${String(id).padStart(3,'0')}`, name:names[i], mobile:`98${String(10000000+i).slice(-8)}`,
    email:`${names[i].toLowerCase().replace(/ /g,'.')}@demo.directcredit.test`, current_city:'Ahmedabad',
    address:`${businesses[i]}, Ahmedabad, Gujarat`, permanent_address:`Ahmedabad, Gujarat`,
    business_name:businesses[i], business_type:'Trading', occupation:'Business', customer_type:'Individual',
    monthly_income:25000+i*3500, years_in_business:2+(i%6), work_experience_years:4+(i%8),
    average_bank_balance:18000+i*4200, primary_bank:banks[i%banks.length], cibil_score:705+(i%8)*9,
    foir:28+(i%5)*6, existing_emi:1200+(i%6)*650, residence_ownership:i%3===0?'Owned':'Rented',
    ownership_proof_status:i%4===0?'verified':'pending', kyc_status:i%5===0?'pending':'verified', email_verified:true,
    pan:`DEMO${String(id).padStart(6,'0')}P`, date_of_birth:'1990-01-15',
    aadhaar_masked:'XXXX-XXXX-12'+String(30+id).slice(-2), gender:i%2?'Female':'Male', marital_status:'Married',
    loan:{id:100+id,customer_id:id,requested_amount:amount,eligible_amount:amount,sanctioned_amount:status==='pending'?0:amount,
      disbursed_amount:status==='pending'?0:amount,outstanding_amount:outstanding,monthly_emi:Math.round(amount/6),
      tenure_months:6,product:'Micro Business Loan',status,current_stage:status==='pending'?'ASSESSMENT':'SERVICING',
      scorecard_score:92+(i%6)*5,scorecard_max:125,scorecard_approval_percent:status==='pending'?null:(i%3===0?80:100)}
  };
});
const DEMO_LOANS = DEMO_CUSTOMERS.map(x=>x.loan);
function demoReporting(){
  const loans=DEMO_LOANS, active=loans.filter(x=>x.status==='active').length, overdue=loans.filter(x=>x.status==='overdue').length;
  const repaid=loans.filter(x=>x.status==='repaid').length, pending=loans.filter(x=>x.status==='pending').length;
  return {
    generated_at:new Date().toISOString(),
    customers:{total:10,active:9,incomplete:2,kyc_verified:8},
    applications:10,unique_users:10,repeat_users:0,pending,rejected:0,disbursed_count:8,active_loans:active,overdue_loans:overdue,repaid_loans:repaid,
    amounts:{disbursed:95000,outstanding:loans.reduce((s,x)=>s+x.outstanding_amount,0),overdue:loans.filter(x=>x.status==='overdue').reduce((s,x)=>s+x.outstanding_amount,0),due:112000,paid:65000,unpaid:47000},
    documents:18,repayments:42,
    recent_loans:loans.map(x=>({id:x.id,customer_id:x.customer_id,customer_name:DEMO_CUSTOMERS[x.customer_id-1].name,amount:x.sanctioned_amount||x.requested_amount,status:x.status,created_at:new Date(Date.now()-(x.customer_id*86400000)).toISOString()})),
    monthly:[{month:'Apr',applications:2,disbursed_count:2,disbursed_amount:17500},{month:'May',applications:3,disbursed_count:2,disbursed_amount:22500},{month:'Jun',applications:2,disbursed_count:2,disbursed_amount:25000},{month:'Jul',applications:3,disbursed_count:2,disbursed_amount:30000}],
    loan_trend:[],slabs:[],repayment_status:{},due_calendar:[],collection:[],collection_agent_performance:[],
    bank_analysis:{transactions:120,credits:450000,debits:380000,negative_balance_events:1,monthly:[],top_categories:[]},
    risk_score:{assessed_loans:8,average_score:106.5,max_score:125,decisions:{APPROVE:7,MANUAL_REVIEW:1},approval_80_90_100:{80:2,90:2,100:4},hard_reject_count:0}
  };
}

window.DirectCreditData = (() => {
  const DEMO_MODE = true;
  const base = (window.DIRECTCREDIT_API_URL || localStorage.getItem('directcredit_api_url') || '/api').replace(/\/$/, '');
  const headers = () => { const token=localStorage.getItem('directcredit_admin_token') || window.DIRECTCREDIT_ADMIN_TOKEN; return token ? {Accept:'application/json',Authorization:`Bearer ${token}`} : {Accept:'application/json'}; };
  async function get(path){const r=await fetch(`${base}${path}`,{headers:headers()});if(!r.ok)throw new Error(`API ${r.status}`);return r.json()}
  async function reporting(){return DEMO_MODE ? demoReporting() : get('/admin/reporting')}
  async function loans(){return DEMO_MODE ? DEMO_LOANS : get('/admin/loans')}
  const parsed=v=>{if(v==null)return v;if(typeof v!=='string')return v;try{return JSON.parse(v)}catch(_){return v}};
  async function customer(id){if(DEMO_MODE){const demo=DEMO_CUSTOMERS.find(x=>Number(x.id)===Number(id))||DEMO_CUSTOMERS[0];return {customer:demo,loans:[demo.loan],metrics:{total_loans:1,total_loan_amount:demo.loan.sanctioned_amount||demo.loan.requested_amount,outstanding_amount:demo.loan.outstanding_amount,amount_paid:Math.max(demo.loan.disbursed_amount-demo.loan.outstanding_amount,0),overdue_amount:demo.loan.status==='overdue'?demo.loan.outstanding_amount:0},bank_analysis:{status:'Demo banking data',average_eod_balance:demo.average_bank_balance,average_monthly_credit:45000,average_monthly_debit:32000,total_transactions:12,negative_balance_count:0},kyc_employment:{kyc_status:demo.kyc_status,employment_type:demo.occupation,income:demo.monthly_income,work_experience_years:demo.work_experience_years,years_in_business:demo.years_in_business,residence_ownership:demo.residence_ownership,ownership_proof_status:demo.ownership_proof_status},risk_score:{total_score:demo.loan.scorecard_score,max_score:125,raw_score:demo.loan.scorecard_score,risk_tier:demo.loan.scorecard_score>=105?'Low Risk':'Moderate Risk',decision:demo.loan.status==='pending'?'MANUAL_REVIEW':'APPROVE',credit_score:demo.cibil_score,source:'scorecard',scorecard_version:'MBL-125-v1',approval_percent:demo.loan.scorecard_approval_percent,reasons:['Demo assessment record'],hard_rejects:[],factor_scores:{}}};} const [cr,lr]=await Promise.all([get(`/customers/${encodeURIComponent(id)}`),loans()]);const rows=lr.filter(x=>Number(x.customer_id)===Number(id));const outstanding=rows.reduce((s,x)=>s+Number(x.outstanding_amount||0),0);const paid=rows.reduce((s,x)=>s+Math.max(Number(x.disbursed_amount||0)-Number(x.outstanding_amount||0),0),0);const overdue=rows.filter(x=>x.status==='overdue').reduce((s,x)=>s+Number(x.outstanding_amount||0),0);const latest=rows[0]||{};return {customer:cr,loans:rows,metrics:{total_loans:rows.length,total_loan_amount:rows.reduce((s,x)=>s+Number(x.sanctioned_amount||x.requested_amount||0),0),outstanding_amount:outstanding,amount_paid:paid,overdue_amount:overdue},bank_analysis:{status:cr.primary_bank?'Customer banking field recorded':'No bank account data connected'},kyc_employment:{kyc_status:cr.kyc_status,employment_type:cr.occupation,income:cr.monthly_income,work_experience_years:cr.work_experience_years,years_in_business:cr.years_in_business,residence_ownership:cr.residence_ownership,ownership_proof_status:cr.ownership_proof_status},risk_score:{total_score:latest.scorecard_score??null,max_score:latest.scorecard_max??125,risk_tier:latest.scorecard_decision==='REJECT'?'High Risk':latest.scorecard_score>=105?'Low Risk':latest.scorecard_score>=95?'Moderate Risk':'Not assessed',decision:latest.scorecard_decision||'Not assessed',credit_score:cr.cibil_score||null,source:latest.scorecard_score!=null?'scorecard':'scorecard_not_configured',scorecard_version:latest.scorecard_version||'MBL-125-v1',approval_percent:latest.scorecard_approval_percent??null,reasons:parsed(latest.scorecard_reasons)||[],hard_rejects:parsed(latest.scorecard_hard_rejects)||[],factor_scores:parsed(latest.scorecard_factor_scores)||{}}};}
  return {base,headers,reporting,customer,loans};
})();
