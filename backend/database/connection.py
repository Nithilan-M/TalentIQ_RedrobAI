import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load env variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to local SQLite if Postgres is not configured
    DATABASE_URL = "sqlite:///./talent_iq.db"
    connect_args = {"check_same_thread": False}
    print(f"Database connection: SQLite fallback ({DATABASE_URL})")
else:
    # Ensure correct postgresql protocol for SQLAlchemy (fix postgreSQL:// to postgres:// if needed, or vice-versa)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    connect_args = {}
    print(f"Database connection: PostgreSQL database detected")

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI dependency to yield database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
