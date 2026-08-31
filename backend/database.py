import os
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "")

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker
except ImportError:
    create_engine = None
    declarative_base = None
    sessionmaker = None

if create_engine and DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
else:
    engine = None
    SessionLocal = None
    Base = None

def get_db() -> Generator:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
