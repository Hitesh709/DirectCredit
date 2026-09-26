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
    loan_trend:[
      {month:'Mar-26',disbursed_amount:12000,loan_count:1},{month:'Apr-26',disbursed_amount:17500,loan_count:2},
      {month:'May-26',disbursed_amount:22500,loan_count:2},{month:'Jun-26',disbursed_amount:25000,loan_count:2},
      {month:'Jul-26',disbursed_amount:30000,loan_count:3},{month:'Aug-26',disbursed_amount:10000,loan_count:1}
    ],
    slabs:[
      {amount:5000,total_count:2,active_count:1,overdue_count:0,repaid_count:1,active_amount:3600,overdue_amount:0,repaid_amount:5000},
      {amount:7500,total_count:2,active_count:1,overdue_count:1,repaid_count:0,active_amount:5400,overdue_amount:4650,repaid_amount:0},
      {amount:10000,total_count:2,active_count:1,overdue_count:1,repaid_count:0,active_amount:7200,overdue_amount:6200,repaid_amount:0},
      {amount:12500,total_count:2,active_count:1,overdue_count:0,repaid_count:1,active_amount:9000,overdue_amount:0,repaid_amount:12500},
      {amount:15000,total_count:2,active_count:1,overdue_count:0,repaid_count:1,active_amount:10800,overdue_amount:0,repaid_amount:15000}
    ],
    repayment_status:{
      'On-Time / Paid':{count:20,due:42000,paid:42000,unpaid:0},
      'Overdue DPD 1–30':{count:8,due:21000,paid:5500,unpaid:15500},
      'Overdue DPD 31–60':{count:4,due:12500,paid:2500,unpaid:10000},
      'Overdue DPD 61–90':{count:2,due:7000,paid:1000,unpaid:6000},
      'NPA DPD 90+':{count:1,due:2500,paid:0,unpaid:2500},
      'Upcoming':{count:7,due:37000,paid:0,unpaid:37000}
    },
    due_calendar:[
      {date:'2026-08-01',count:4,due:31500,paid:21000},
      {date:'2026-08-02',count:3,due:22500,paid:14500},
      {date:'2026-08-03',count:5,due:49300,paid:32300},
      {date:'2026-08-04',count:4,due:50800,paid:32500},
      {date:'2026-08-05',count:4,due:55000,paid:36000},
      {date:'2026-08-06',count:3,due:46300,paid:27000},
      {date:'2026-08-07',count:3,due:38600,paid:24500},
      {date:'2026-08-08',count:4,due:46000,paid:29200}
    ],
    collection:[
      {date:'2026-03',collected:24500,efficiency:89.2},{date:'2026-04',collected:28500,efficiency:91.3},
      {date:'2026-05',collected:30200,efficiency:92.6},{date:'2026-06',collected:31200,efficiency:92.7},
      {date:'2026-07',collected:32600,efficiency:93.1},{date:'2026-08',collected:38500,efficiency:96.4}
    ],
    collection_agent_performance:[
      {agent_code:'ACT001',name:'Ramesh Shah',actions:42,receipts:18,collected_amount:8200,efficiency:94.5},
      {agent_code:'ACT002',name:'Sunil Patel',actions:38,receipts:16,collected_amount:7600,efficiency:91.4},
      {agent_code:'ACT003',name:'Amit Kumar',actions:35,receipts:15,collected_amount:6900,efficiency:90.0},
      {agent_code:'ACT004',name:'Meena Joshi',actions:31,receipts:13,collected_amount:6200,efficiency:88.7},
      {agent_code:'ACT005',name:'Ankit Verma',actions:29,receipts:12,collected_amount:5700,efficiency:86.9},
      {agent_code:'ACT006',name:'Pooja Mehta',actions:27,receipts:11,collected_amount:5200,efficiency:87.5}
    ],
    recent_repayments:DEMO_LOANS.slice(0,8).map((x,i)=>({loan_id:x.id,customer_id:x.customer_id,loan_amount:x.disbursed_amount,paid_amount:Math.round((x.disbursed_amount||0)*0.18),date:'2026-08-'+String(10+i).padStart(2,'0'),status:'SUCCESS'})),
    bank_analysis:{transactions:120,credits:450000,debits:380000,negative_balance_events:1,monthly:[
      {month:'Mar-26',credits:72000,debits:59000,transactions:18,average_balance:18500},
      {month:'Apr-26',credits:78000,debits:62000,transactions:20,average_balance:21400},
      {month:'May-26',credits:69000,debits:57000,transactions:17,average_balance:22800},
      {month:'Jun-26',credits:84000,debits:71000,transactions:22,average_balance:25100},
      {month:'Jul-26',credits:91000,debits:76000,transactions:23,average_balance:27400},
      {month:'Aug-26',credits:56000,debits:55000,transactions:20,average_balance:29100}
    ],top_categories:[['Business Payments',182000],['Supplier Payments',94000],['Cash Withdrawals',68000],['UPI / Loan Repayment',52000],['Utilities & Rent',34000],['Others',30000]]},
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
