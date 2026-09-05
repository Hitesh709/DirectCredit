# DirectCredit — Tasks 111–115

## Phase 12 — Sample Loan Flow Completion

111. **Official 125-point score persistence** — calculate the supplied MBL scorecard on the backend, persist score/version/decision/approval percentage/factor scores/reason codes, and expose the breakdown to admin/customer views.
112. **Complete matrix reporting** — return monthly application/disbursement data, loan-slab performance, repayment status buckets and due-calendar data used by the sample dashboard.
113. **Collection operations** — persist collection agents/actions, expose agent performance, create authorized debit requests without moving funds, and post collection receipts into the canonical repayment ledger.
114. **Bank statement analysis** — persist actual bank transactions and expose credits/debits, monthly cash flow, average balances, negative-balance events, categories and transaction detail. No synthetic banking values are generated.
115. **Sample-flow UI wiring** — display the persisted scorecard, bank analysis, matrix data and live collection controls in the corresponding sample screens.

## Source rule
The supplied framework states a 125-point maximum but its listed factor maxima total 130 before the +5 both-owned bonus. The implementation therefore preserves all listed factors, records the raw score, and caps the published score at the stated 125 maximum. This discrepancy is surfaced in code rather than silently deleting a factor.
