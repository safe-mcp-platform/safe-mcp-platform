"""
safe-mcp-sdk: Security SDK for MCP Server Developers

Makes it dead simple to build secure MCP servers using SAFE-MCP techniques.
Just add @secure() decorator to your tools!
"""

from .decorators import secure
from .exceptions import SAFEMCPException
from .validators import SAFEMCPValidator

# Alias for compatibility with official SDK examples
secure_tool = secure
secure_mcp_server = secure

__version__ = "1.0.0"
__all__ = ["secure", "secure_tool", "secure_mcp_server", "SAFEMCPException", "SAFEMCPValidator"]

