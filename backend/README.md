# DirectCredit Backend

FastAPI backend foundation for the DirectCredit micro-business loan application.

## Current product
- Loan amount: ₹5,000–₹15,000
- Monthly repayment
- Demo external verification/payment integrations pending

## Render
- Root directory: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`

## Important
This repository is an MVP foundation. Real PAN/Aadhaar/bureau/e-sign/bank integrations, persistent production authentication, secure object storage, audit controls, and production payment/mandate flows must be completed and validated before handling live customer financial data.
