#!/usr/bin/env python3
"""
Start Gateway Service
Entry point for SAFE-MCP Gateway (MCP Multiplexer)
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.gateway_service_enhanced import main

if __name__ == "__main__":
    main()

