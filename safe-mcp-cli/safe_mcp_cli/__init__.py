"""
SAFE-MCP CLI - Professional Security for Model Context Protocol

Transparent runtime protection for MCP deployments with 4-channel threat detection.

Features:
- Auto-discovery of MCP clients (Claude, Cursor, Windsurf, VS Code)
- Transparent gateway injection (no code changes)
- 4-channel detection (Pattern + Rules + ML + Behavioral)
- Professional CLI interface
- Whitelist management
- Protection status tracking

Example Usage:
    from safe_mcp_cli.discovery import discover_all_configs
    from safe_mcp_cli.gateway import wrap_client_config
    
    # Discover clients
    configs = discover_all_configs()
    
    # Protect a client
    wrap_client_config(configs[0].config_path)

CLI Usage:
    safe-mcp scan                    # Discover MCP clients
    safe-mcp protect cursor          # Enable protection
    safe-mcp status                  # Check status
    safe-mcp dashboard               # Open admin UI
"""

__version__ = "1.0.0"
__author__ = "SAFE-MCP Platform Team"
__license__ = "MIT"

from safe_mcp_cli.discovery.client_discovery import (
    ClientInfo,
    DiscoveredConfig,
    discover_all_configs,
    display_discovered_configs,
    get_client_by_name,
)
from safe_mcp_cli.gateway.config_injector import (
    InjectionConfig,
    MCPConfigInjector,
    unwrap_client_config,
    wrap_client_config,
)
from safe_mcp_cli.storage.storage_manager import (
    ProtectionState,
    StorageManager,
    UserConfig,
    WhitelistEntry,
    get_storage,
)

__all__ = [
    # Discovery
    "ClientInfo",
    "DiscoveredConfig",
    "discover_all_configs",
    "display_discovered_configs",
    "get_client_by_name",
    # Gateway
    "InjectionConfig",
    "MCPConfigInjector",
    "wrap_client_config",
    "unwrap_client_config",
    # Storage
    "StorageManager",
    "WhitelistEntry",
    "UserConfig",
    "ProtectionState",
    "get_storage",
]

