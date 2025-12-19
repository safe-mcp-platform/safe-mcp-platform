"""
Database Connection Management
Production-grade connection pooling
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import structlog

from config import settings
from .models import Base

logger = structlog.get_logger()

# Global engine instance
engine = None
SessionLocal = None


def init_db():
    """Initialize database connection and create tables."""
    global engine, SessionLocal
    
    logger.info("Initializing database connection", url=settings.DATABASE_URL.split("@")[1])  # Hide password
    
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,  # Verify connections before using
        echo=settings.DEBUG,
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database initialized successfully")


def close_db():
    """Close database connections."""
    global engine
    
    if engine:
        logger.info("Closing database connections")
        engine.dispose()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get database session with automatic cleanup.
    
    Usage:
        with get_db() as db:
            db.query(Detection).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Database transaction failed", error=str(e))
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # FastAPI will handle cleanup


def get_admin_db_session() -> Session:
    """Get database session for admin service."""
    return SessionLocal()


def get_engine():
    """Get database engine."""
    return engine
