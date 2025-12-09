"""
Database connection and session management using SQLModel.
"""
from sqlmodel import create_engine, SQLModel, Session
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/docupilot")

# Create engine with connection pool settings for Neon/cloud databases
# These settings help with connection stability
# Note: If DATABASE_URL already contains query parameters, they will be used
# We don't override them in connect_args to avoid conflicts

# Parse DATABASE_URL to check if it already has SSL settings
connect_args = {}
if "sslmode" not in DATABASE_URL:
    connect_args["sslmode"] = "require"
if "connect_timeout" not in DATABASE_URL:
    connect_args["connect_timeout"] = 10

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Verify connections before using them (important for Neon)
    pool_recycle=300,    # Recycle connections after 5 minutes
    pool_size=5,         # Number of connections to maintain
    max_overflow=10,     # Additional connections if needed
    connect_args=connect_args if connect_args else {}
)

def init_db():
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Use with FastAPI Depends().
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
