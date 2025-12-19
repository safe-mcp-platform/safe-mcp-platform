"""
SAFE-MCP Client Package
Python client for SAFE-MCP Platform
"""

__version__ = "1.0.0"

from .client import SafeMCPClient
from .gateway_client import GatewayClient

__all__ = ["SafeMCPClient", "GatewayClient", "__version__"]

