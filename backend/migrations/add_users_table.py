#!/usr/bin/env python3
"""
Migration: Create users table
"""

from database.connection import get_db_session, init_db, get_engine
from database.models import Base, User
import structlog

logger = structlog.get_logger()


def upgrade():
    """Create users table"""
    try:
        init_db()
        engine = get_engine()
        logger.info("Creating users table...")
        Base.metadata.create_all(bind=engine, tables=[User.__table__])
        logger.info("✅ Migration complete: Created users table")
    except Exception as e:
        logger.error("Migration failed", error=str(e))
        raise


def downgrade():
    """Drop users table"""
    try:
        init_db()
        engine = get_engine()
        logger.info("Dropping users table...")
        User.__table__.drop(engine)
        logger.info("✅ Downgrade complete: Dropped users table")
    except Exception as e:
        logger.error("Downgrade failed", error=str(e))
        raise


if __name__ == "__main__":
    upgrade()

