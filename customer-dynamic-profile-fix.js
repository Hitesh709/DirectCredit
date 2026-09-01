/* DirectCredit customer profile identity fix.
   New login IDs create an empty, customer-specific profile. No random person or loan data is generated. */
(function(){
  const STORE='dcCustomerProfiles';
  function read(){try{return JSON.parse(localStorage.getItem(STORE)||'{}')}catch(e){return {}}}
  function write(p){localStorage.setItem(STORE,JSON.stringify(p))}
  function displayNameFromId(id){
    const raw=String(id||'').trim();
    if(!raw) return 'New Customer';
    // Mobile numbers/customer codes remain identifiers; ordinary text IDs become a readable name.
    if(/^\+?\d+$/.test(raw) || /^CUST\d+$/i.test(raw)) return raw.toUpperCase();
    return raw.replace(/[._-]+/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
  }
  function emptyProfile(customerId){
    const id=String(customerId||'').trim();
    return {
      customerId:id,
      name:displayNameFromId(id),
      mobile:'—', email:'—', address:'—', businessName:'—', businessType:'—',
      monthlyIncome:0, bank:'—', averageBalance:0, cibil:0, foir:0, existingEmi:0,
      score:'—', risk:'Pending', activeLoans:0, sanctioned:0, outstanding:0, emi:0, nextDue:'—',
      applicationId:'', status:'New', createdAt:new Date().toISOString(),
      panStatus:'Pending', aadhaarStatus:'Pending', bankStatus:'Pending',
      journey:{done:[],current:0}, loans:[], repayments:[],
      documents:[
        {name:'PAN Card',value:'Not entered',status:'Pending'},
        {name:'Aadhaar Card',value:'Not uploaded',status:'Pending'},
        {name:'Bank Statement',value:'Not uploaded',status:'Pending'},
        {name:'Business Proof',value:'Not uploaded',status:'Pending'}
      ],
      profileSource:'customer-login'
    };
  }
  function isOldGeneratedProfile(p){
    if(!p) return false;
    const oldNames=['Amit Patel','Neha Shah','Rahul Mehta','Priya Desai','Vivek Joshi','Anita Verma'];
    return oldNames.includes(p.name) && /@example\.com$/i.test(String(p.email||'')) && String(p.address||'').includes('23, Patel Street, Ahmedabad');
  }
  window.createProfile=function(customerId){return emptyProfile(customerId)};
  window.getCustomerProfile=function(customerId){
    const id=String(customerId||'').trim();
    const profiles=read();
    if(!profiles[id] || isOldGeneratedProfile(profiles[id])){
      profiles[id]=emptyProfile(id);
      write(profiles);
    }
    return profiles[id];
  };
})();
