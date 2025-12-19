"""
Migration: Add token columns to users table
"""

import structlog
from sqlalchemy import text
from database.connection import init_db, get_engine

logger = structlog.get_logger()

def upgrade():
    """Add token columns"""
    init_db()
    engine = get_engine()
    
    logger.info("Adding token columns to users table...")
    
    with engine.connect() as conn:
        # Add columns if they don't exist
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS current_token VARCHAR(255)
        """))
        
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMP WITH TIME ZONE
        """))
        
        conn.commit()
    
    logger.info("✅ Token columns added successfully")

def downgrade():
    """Remove token columns"""
    init_db()
    engine = get_engine()
    
    logger.info("Removing token columns from users table...")
    
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS current_token"))
        conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS token_expires_at"))
        conn.commit()
    
    logger.info("✅ Token columns removed")

if __name__ == "__main__":
    upgrade()

