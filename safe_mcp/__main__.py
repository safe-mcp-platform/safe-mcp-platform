"""
SAFE-MCP Package Entry Point
Allows running: python -m safe_mcp.gateway_client
"""

import sys
import asyncio
from .gateway_client import main

if __name__ == "__main__":
    # Check which module was requested
    if len(sys.argv) > 1 and sys.argv[1] == "gateway_client":
        asyncio.run(main())
    else:
        print("Usage: python -m safe_mcp.gateway_client")
        sys.exit(1)

