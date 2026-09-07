from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from pathlib import Path

# Database configuration: use DATABASE_URL env var if set, otherwise use local SQLite
_default_db_dir = Path(__file__).resolve().parent.parent.parent / "data" / "db"
_default_db_dir.mkdir(parents=True, exist_ok=True)
_default_db_url = f"sqlite:///{_default_db_dir}/aerorecon.db"

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", _default_db_url)

# SQLite-specific: fix for Render if using SQLite on ephemeral disk
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
