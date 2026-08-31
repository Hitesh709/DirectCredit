from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="DirectCredit API", version="0.1.0")

origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"application": "DirectCredit", "status": "online"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/version")
def version():
    return {"name": "DirectCredit API", "version": "0.1.0"}
