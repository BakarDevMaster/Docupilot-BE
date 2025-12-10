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

# Lazy engine creation - only create when needed
_engine = None

def get_engine():
    """Get or create database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        # Parse DATABASE_URL to check if it already has SSL settings
        connect_args = {}
        if "sslmode" not in DATABASE_URL:
            connect_args["sslmode"] = "require"
        if "connect_timeout" not in DATABASE_URL:
            connect_args["connect_timeout"] = 10
        
        _engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,  # Verify connections before using them (important for Neon)
            pool_recycle=300,    # Recycle connections after 5 minutes
            pool_size=5,         # Number of connections to maintain
            max_overflow=10,     # Additional connections if needed
            connect_args=connect_args if connect_args else {}
        )
    return _engine

# For backward compatibility - lazy initialization only
# Don't create engine on import to avoid serverless cold start issues
engine = None

def _lazy_init_engine():
    """Lazy initialization of engine for backward compatibility."""
    global engine
    if engine is None:
        try:
            if DATABASE_URL and "postgresql://" in DATABASE_URL:
                engine = get_engine()
            else:
                engine = None
        except Exception as e:
            print(f"Warning: Could not initialize database engine: {e}")
            engine = None
    return engine

def init_db():
    """Initialize database tables."""
    db_engine = get_engine()
    if db_engine:
        SQLModel.metadata.create_all(db_engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Use with FastAPI Depends().
    """
    db_engine = get_engine()
    if db_engine is None:
        raise Exception("Database engine not initialized. Check DATABASE_URL environment variable.")
    session = Session(db_engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
