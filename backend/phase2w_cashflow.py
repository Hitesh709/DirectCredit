"""Phase 2W - Banking & Cashflow Intelligence."""
PHASE2W_VERSION="MBL-CASHFLOW-2W-v1"
def analyze_transactions(transactions:list[dict])->dict:
 credits=debits=0.0; balances=[]; bounces=0
 for t in transactions or []:
  a=abs(float(t.get("amount") or 0)); direction=str(t.get("direction") or "").lower()
  if direction in {"credit","cr","in"}: credits+=a
  elif direction in {"debit","dr","out"}: debits+=a
  if t.get("balance") is not None: balances.append(float(t["balance"]))
  if str(t.get("category") or "").lower() in {"bounce","emi_bounce","ecs_return"}: bounces+=1
 return {"version":PHASE2W_VERSION,"transaction_count":len(transactions or []),"total_credits":round(credits,2),"total_debits":round(debits,2),"net_cashflow":round(credits-debits,2),"average_balance":round(sum(balances)/len(balances),2) if balances else 0,"bounce_count":bounces,"credit_debit_ratio":round(credits/debits,3) if debits else None}
def contract(): return {"version":PHASE2W_VERSION,"purpose":"Evidence-based bank transaction and cashflow analytics","outputs":["credits","debits","net_cashflow","average_balance","bounces","credit_debit_ratio"],"rules":["Transaction count is not a proxy for month coverage","No fabricated bank data"]}