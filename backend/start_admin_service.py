#!/usr/bin/env python3
"""
Start Admin Service
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.admin_service import app
import uvicorn
from config import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.ADMIN_PORT,
        log_level="info"
    )

