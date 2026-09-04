# DirectCredit — 100-Task Build Plan

This is the master implementation sequence for the full DirectCredit lending platform. Tasks are ordered so the data foundation is completed before UI/reporting/automation layers.

## Phase 1 — Foundation & Data Integrity (1–10)
1. Establish one source of truth for customer, loan, document and repayment data; remove static customer identity from login flow.
2. Define canonical customer identity and login/session contract.
3. Define canonical loan lifecycle/status/stage contract.
4. Define document metadata and ownership contract.
5. Define repayment/collection contract.
6. Add database migration/versioning strategy.
7. Add API error and validation standard.
8. Add audit-event model and API.
9. Add environment/configuration contract for local, Vercel and Render.
10. Add automated smoke-test foundation for API and portal.

## Phase 2 — Customer Authentication & Profile (11–20)
11. Build real customer login by customer ID/mobile + password/OTP abstraction.
12. Build customer logout/session expiry.
13. Build new-customer registration/profile creation.
14. Build editable personal profile: name, DOB, gender, occupation.
15. Build employment/business profile: company, business type, income and experience.
16. Build current and permanent address management.
17. Build residence ownership: own/rented/family/company/other.
18. Build residence/ownership proof upload and metadata.
19. Build customer profile validation and completion score.
20. Sync every customer profile change to Admin in real time/API-first fashion.

## Phase 3 — 13-Step Customer Loan Journey (21–30)
21. PAN entry and verification adapter.
22. Aadhaar OCR/verification adapter.
23. Selfie/liveness adapter.
24. Bureau/CIBIL adapter.
25. Profile completion step.
26. Bank statement upload and analysis.
27. Other-document upload and verification.
28. Loan assessment and eligibility.
29. Sanction and customer approval.
30. E-sign → disbursement → repayment lifecycle completion.

## Phase 4 — Loan Request & Eligibility Engine (31–40)
31. Loan request form.
32. Product selection.
33. Requested amount and tenure validation.
34. Micro-business eligibility scorecard.
35. Auto-approval threshold rules.
36. Income/FOIR calculation.
37. Bureau/risk score calculation.
38. Banking behaviour score calculation.
39. Eligibility amount calculation.
40. Approval/decline/refer decision engine with reasons.

## Phase 5 — Admin Customer & Loan Operations (41–50)
41. Customer list/search/filter.
42. Customer profile with all five profile tabs.
43. Customer journey/KYC status view.
44. Customer documents view.
45. Customer loan history.
46. Loan request & eligibility admin tab.
47. Loan application management.
48. Sanction/approval management.
49. E-sign/e-mandate tracking.
50. Disbursement management.

## Phase 6 — Loan Servicing & Collections (51–60)
51. Loan account ledger.
52. Disbursement records.
53. EMI schedule generation.
54. Repayment posting.
55. Partial payment support.
56. Prepayment/foreclosure calculation.
57. DPD calculation.
58. Overdue/bounce tracking.
59. Collection allocation and receipts.
60. Loan closure/NOC workflow.

## Phase 7 — Admin Dashboard & Analytics (61–70)
61. Dynamic admin dashboard cards from database.
62. Applications dashboard.
63. Customer analytics.
64. Loan pipeline page.
65. Disbursement matrix page.
66. Loan slab performance page.
67. Repayment matrix page.
68. Due calendar page.
69. Loan trend & summary page.
70. Risk & score analytics page.

## Phase 8 — Reports, Accounting & Risk (71–80)
71. Registration & users report.
72. Loan pipeline report.
73. Disbursement report.
74. Repayment/collection report.
75. Accounting ledger.
76. Bank analysis report.
77. Risk & score breakdown.
78. Portfolio quality/DPD report.
79. Export CSV/PDF/print views.
80. Reconciliation controls.

## Phase 9 — Documents, Alerts, Settings & Support (81–90)
81. Central document repository.
82. Document preview/download.
83. Verification status workflow.
84. Alerts/notifications center.
85. Customer SMS/email adapter abstraction.
86. Admin settings.
87. Product/rule configuration.
88. User/role permissions.
89. Support/ticket workflow.
90. System activity/audit log UI.

## Phase 10 — Production Readiness & Deployment (91–100)
91. Replace all remaining hardcoded business/customer numbers with API/database values.
92. Replace all demo-only identity assumptions.
93. Add API provider abstraction for PAN/Aadhaar/bureau/bank data.
94. Add secure file storage abstraction.
95. Add production database configuration.
96. Add backup/restore procedure.
97. Add security headers, rate limits and input sanitization.
98. Add end-to-end customer/admin regression tests.
99. Deploy and verify Vercel + backend architecture, environment variables and health checks.
100. Final production audit: every menu, tab, form, API, record, calculation and report must use the same underlying data.

## Current status
- Tasks 1–30: **COMPLETE**
- Tasks 31–40: **COMPLETE — backend eligibility contracts implemented; official 125-point scorecard/provider inputs remain explicit dependencies**
- Tasks 41–50: **COMPLETE — canonical admin customer/loan operation contracts implemented**
- Tasks 51–60: **IMPLEMENTED — servicing, disbursement, ledger, repayment, partial payment, foreclosure, DPD, collections and closure APIs added**
- Tasks 61–70: **IMPLEMENTED — database-backed admin analytics endpoints added**
- Tasks 71–75: **IMPLEMENTED — secured registration, pipeline, disbursement, repayment/collection and accounting reports added**
- Tasks 76–80: **IMPLEMENTED — bank analysis, risk breakdown, portfolio quality/DPD, CSV exports and reconciliation APIs added**
- Tasks 81–90: **IMPLEMENTED — document repository, notification/settings/permissions/support/audit API contracts added; existing document service remains the source of truth**
- Tasks 91–98: **IMPLEMENTED — production source-of-truth checks, provider boundary, file-storage boundary, production configuration guidance, backup/restore procedure, security controls and expanded smoke-test suite added**
- Tasks 99–100: **READY FOR LIVE VERIFICATION — health/readiness endpoints and final-audit checklist are present; live Vercel/Render verification remains an environment-level check**

## Non-negotiable project rules
1. No static customer identity in the customer portal.
2. No static dashboard/loan/repayment totals when database/API data exists.
3. Every customer action must be attributable to the logged-in customer ID.
4. Every loan must belong to a customer.
5. Documents must belong to a customer and optionally a loan.
6. Admin and Customer Portal must read the same source of truth.
7. UI changes must not break existing tabs/routes.
8. Demo mode must be clearly separated from production/provider integrations.
9. Never expose passwords, PAN/Aadhaar full values or secrets in API responses/logs.
10. Each completed task must be committed and smoke-tested before moving to the next task.
