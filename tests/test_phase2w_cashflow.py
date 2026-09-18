from backend.phase2w_cashflow import analyze_transactions
def test_cashflow(): assert analyze_transactions([{'amount':100,'direction':'credit'},{'amount':40,'direction':'debit'}])['net_cashflow']==60