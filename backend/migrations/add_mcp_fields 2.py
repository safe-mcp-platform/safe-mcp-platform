"""
Migration: Add MCP-specific fields to detections table
"""

from sqlalchemy import text
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_admin_db_session, init_db


def upgrade():
    """Add MCP-specific columns to detections table"""
    # Initialize database first
    init_db()
    
    db = get_admin_db_session()
    
    try:
        # Add MCP columns
        migrations = [
            "ALTER TABLE detections ADD COLUMN IF NOT EXISTS mcp_method VARCHAR(50)",
            "ALTER TABLE detections ADD COLUMN IF NOT EXISTS mcp_tool_name VARCHAR(255)",
            "ALTER TABLE detections ADD COLUMN IF NOT EXISTS mcp_tool_arguments JSON",
            "ALTER TABLE detections ADD COLUMN IF NOT EXISTS mcp_server_name VARCHAR(100)",
        ]
        
        for migration_sql in migrations:
            db.execute(text(migration_sql))
        
        # Add indexes
        index_migrations = [
            "CREATE INDEX IF NOT EXISTS idx_mcp_method ON detections(mcp_method)",
            "CREATE INDEX IF NOT EXISTS idx_mcp_tool_name ON detections(mcp_tool_name)",
        ]
        
        for index_sql in index_migrations:
            db.execute(text(index_sql))
        
        db.commit()
        print("✅ Migration complete: Added MCP fields to detections table")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()


def downgrade():
    """Remove MCP-specific columns"""
    # Initialize database first
    init_db()
    
    db = get_admin_db_session()
    
    try:
        # Remove indexes first
        db.execute(text("DROP INDEX IF EXISTS idx_mcp_method"))
        db.execute(text("DROP INDEX IF EXISTS idx_mcp_tool_name"))
        
        # Remove columns
        columns = ["mcp_method", "mcp_tool_name", "mcp_tool_arguments", "mcp_server_name"]
        for column in columns:
            db.execute(text(f"ALTER TABLE detections DROP COLUMN IF EXISTS {column}"))
        
        db.commit()
        print("✅ Downgrade complete: Removed MCP fields")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Downgrade failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()

