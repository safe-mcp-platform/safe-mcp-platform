"""
MCP Config Injector - Transparent Gateway Wrapper

Automatically wraps MCP servers with safe-mcp-gateway for runtime protection.
Inspired by mcp-scan's gateway injection with enhancements.

Key Features:
- Transparent wrapping (no user code changes)
- Reversible (clean uninstall)
- Multi-client support (Claude, Cursor, Windsurf, VSCode)
- Backup/restore of original configs
"""

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import rich
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

console = Console()


@dataclass
class MCPServer:
    """An MCP server configuration."""

    name: str
    command: str
    args: list[str]
    env: Optional[dict[str, str]] = None


@dataclass
class InjectionConfig:
    """Configuration for gateway injection."""

    gateway_url: str = "http://localhost:8002"
    detection_url: str = "http://localhost:8001"
    admin_url: str = "http://localhost:8000"
    enable_logging: bool = True
    enable_blocking: bool = True


class MCPConfigInjector:
    """Handles injection and removal of safe-mcp-gateway wrapper."""

    BACKUP_SUFFIX = ".safe-mcp-backup"
    WRAPPED_MARKER = "# SAFE-MCP-WRAPPED"

    def __init__(self, config_path: str):
        """
        Initialize the injector.

        Args:
            config_path: Path to the MCP config file
        """
        self.config_path = os.path.expanduser(config_path)
        self.backup_path = self.config_path + self.BACKUP_SUFFIX

    def is_wrapped(self) -> bool:
        """Check if the config is already wrapped."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                content = f.read()
                return self.WRAPPED_MARKER in content
        except Exception:
            return False

    def backup_config(self) -> bool:
        """
        Create a backup of the original config.

        Returns:
            True if backup was created, False if backup already exists
        """
        if os.path.exists(self.backup_path):
            console.print(f"[yellow]⚠️  Backup already exists: {self.backup_path}[/yellow]")
            return False

        shutil.copy2(self.config_path, self.backup_path)
        console.print(f"[green]✓[/green] Backup created: {self.backup_path}")
        return True

    def restore_config(self) -> bool:
        """
        Restore the original config from backup.

        Returns:
            True if restore was successful, False if no backup exists
        """
        if not os.path.exists(self.backup_path):
            console.print(f"[red]✗[/red] No backup found: {self.backup_path}")
            return False

        shutil.copy2(self.backup_path, self.config_path)
        os.remove(self.backup_path)
        console.print(f"[green]✓[/green] Config restored from backup")
        return True

    def read_config(self) -> dict[str, Any]:
        """Read and parse the MCP config file."""
        with open(self.config_path, encoding="utf-8") as f:
            return json.load(f)

    def write_config(self, config: dict[str, Any], add_marker: bool = True) -> None:
        """
        Write the MCP config file.

        Args:
            config: Config dictionary
            add_marker: Add wrapped marker comment
        """
        # Add marker to track that this config is wrapped
        if add_marker:
            config["_safe_mcp_metadata"] = {
                "wrapped": True,
                "wrapped_at": datetime.now().isoformat(),
                "version": "1.0.0",
            }

        with open(self.config_path, "w", encoding="utf-8") as f:
            # Write marker comment
            if add_marker:
                f.write(f"{self.WRAPPED_MARKER}\n")
            json.dump(config, f, indent=2)

    def wrap_server(self, server_config: dict[str, Any], injection_config: InjectionConfig) -> dict[str, Any]:
        """
        Wrap a single server config with safe-mcp-gateway.

        Original config:
        {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me"]
        }

        Wrapped config:
        {
          "command": "python",
          "args": [
            "-m", "safe_mcp_gateway.cli",
            "--upstream-command", "npx",
            "--upstream-args", "-y,@modelcontextprotocol/server-filesystem,/Users/me",
            "--gateway-url", "http://localhost:8002",
            "--detection-url", "http://localhost:8001"
          ]
        }

        Args:
            server_config: Original server configuration
            injection_config: Gateway injection settings

        Returns:
            Wrapped server configuration
        """
        original_command = server_config.get("command", "")
        original_args = server_config.get("args", [])
        original_env = server_config.get("env", {})

        # Build wrapped config
        wrapped_args = [
            "-m",
            "safe_mcp_gateway.cli",
            "--upstream-command",
            original_command,
        ]

        if original_args:
            # Join args with comma (we'll split in gateway)
            wrapped_args.extend(["--upstream-args", ",".join(original_args)])

        wrapped_args.extend(
            [
                "--gateway-url",
                injection_config.gateway_url,
                "--detection-url",
                injection_config.detection_url,
            ]
        )

        if injection_config.enable_logging:
            wrapped_args.append("--enable-logging")

        if injection_config.enable_blocking:
            wrapped_args.append("--enable-blocking")

        wrapped_config = {
            "command": "python",
            "args": wrapped_args,
        }

        # Preserve env vars
        if original_env:
            wrapped_config["env"] = original_env

        # Store original for unwrapping
        wrapped_config["_safe_mcp_original"] = {
            "command": original_command,
            "args": original_args,
            "env": original_env,
        }

        return wrapped_config

    def wrap_all_servers(self, injection_config: InjectionConfig) -> tuple[int, int]:
        """
        Wrap all servers in the config.

        Args:
            injection_config: Gateway injection settings

        Returns:
            Tuple of (wrapped_count, total_count)
        """
        if self.is_wrapped():
            console.print("[yellow]⚠️  Config is already wrapped. Use 'unwrap' first.[/yellow]")
            return 0, 0

        # Backup first
        self.backup_config()

        # Read config
        config = self.read_config()

        # Find servers (handle different formats)
        servers = None
        if "mcpServers" in config:
            servers = config["mcpServers"]
        elif "mcp" in config and isinstance(config["mcp"], dict) and "servers" in config["mcp"]:
            # VSCode settings.json format
            servers = config["mcp"]["servers"]

        if not servers:
            console.print("[red]✗[/red] No servers found in config")
            return 0, 0

        # Wrap each server
        wrapped_count = 0
        total_count = len(servers)

        for server_name, server_config in servers.items():
            if isinstance(server_config, dict):
                servers[server_name] = self.wrap_server(server_config, injection_config)
                wrapped_count += 1

        # Write wrapped config
        self.write_config(config, add_marker=True)

        return wrapped_count, total_count

    def unwrap_all_servers(self) -> tuple[int, int]:
        """
        Remove safe-mcp-gateway wrapping from all servers.

        Returns:
            Tuple of (unwrapped_count, total_count)
        """
        if not self.is_wrapped():
            console.print("[yellow]⚠️  Config is not wrapped. Nothing to unwrap.[/yellow]")
            return 0, 0

        # Restore from backup if available
        if os.path.exists(self.backup_path):
            self.restore_config()
            # Count servers for reporting
            config = self.read_config()
            servers = config.get("mcpServers") or (config.get("mcp", {}).get("servers", {}))
            total_count = len(servers) if servers else 0
            return total_count, total_count
        else:
            # Manual unwrap (extract original configs)
            config = self.read_config()
            servers = config.get("mcpServers") or (config.get("mcp", {}).get("servers", {}))

            if not servers:
                return 0, 0

            unwrapped_count = 0
            total_count = len(servers)

            for server_name, server_config in servers.items():
                if isinstance(server_config, dict) and "_safe_mcp_original" in server_config:
                    original = server_config["_safe_mcp_original"]
                    servers[server_name] = {
                        "command": original["command"],
                        "args": original["args"],
                    }
                    if original.get("env"):
                        servers[server_name]["env"] = original["env"]
                    unwrapped_count += 1

            # Remove metadata
            if "_safe_mcp_metadata" in config:
                del config["_safe_mcp_metadata"]

            # Write unwrapped config
            self.write_config(config, add_marker=False)

            return unwrapped_count, total_count


def wrap_client_config(
    config_path: str,
    injection_config: Optional[InjectionConfig] = None,
    verbose: bool = True,
) -> bool:
    """
    Wrap a client's MCP config with safe-mcp-gateway.

    Args:
        config_path: Path to the MCP config file
        injection_config: Gateway injection settings (uses defaults if None)
        verbose: Print detailed output

    Returns:
        True if wrapping was successful
    """
    if injection_config is None:
        injection_config = InjectionConfig()

    injector = MCPConfigInjector(config_path)

    if verbose:
        console.print(f"\n[bold cyan]🔒 Wrapping MCP Config[/bold cyan]")
        console.print(f"[dim]Config: {config_path}[/dim]\n")

    wrapped_count, total_count = injector.wrap_all_servers(injection_config)

    if wrapped_count > 0:
        if verbose:
            console.print(
                Panel(
                    f"[green]✅ Successfully wrapped {wrapped_count}/{total_count} servers[/green]\n\n"
                    f"[dim]Gateway URL: {injection_config.gateway_url}[/dim]\n"
                    f"[dim]Detection URL: {injection_config.detection_url}[/dim]\n"
                    f"[dim]Admin Dashboard: {injection_config.admin_url}[/dim]\n\n"
                    f"[yellow]⚠️  Your MCP client will now route all traffic through safe-mcp-gateway.[/yellow]\n"
                    f"[dim]To remove protection: safe-mcp unwrap[/dim]",
                    title="🛡️  Protection Enabled",
                    border_style="green",
                )
            )
        return True
    else:
        if verbose:
            console.print("[red]✗[/red] No servers were wrapped")
        return False


def unwrap_client_config(config_path: str, verbose: bool = True) -> bool:
    """
    Remove safe-mcp-gateway wrapping from a client's config.

    Args:
        config_path: Path to the MCP config file
        verbose: Print detailed output

    Returns:
        True if unwrapping was successful
    """
    injector = MCPConfigInjector(config_path)

    if verbose:
        console.print(f"\n[bold cyan]🔓 Unwrapping MCP Config[/bold cyan]")
        console.print(f"[dim]Config: {config_path}[/dim]\n")

    unwrapped_count, total_count = injector.unwrap_all_servers()

    if unwrapped_count > 0:
        if verbose:
            console.print(
                Panel(
                    f"[green]✅ Successfully unwrapped {unwrapped_count}/{total_count} servers[/green]\n\n"
                    f"[dim]Original configuration has been restored.[/dim]\n"
                    f"[yellow]⚠️  MCP traffic is no longer protected by safe-mcp-gateway.[/yellow]",
                    title="🔓 Protection Disabled",
                    border_style="yellow",
                )
            )
        return True
    else:
        if verbose:
            console.print("[yellow]⚠️  No servers were unwrapped[/yellow]")
        return False


if __name__ == "__main__":
    # Test the injector
    import sys

    if len(sys.argv) < 3:
        print("Usage: python config_injector.py <wrap|unwrap> <config_path>")
        sys.exit(1)

    action = sys.argv[1]
    config_path = sys.argv[2]

    if action == "wrap":
        wrap_client_config(config_path)
    elif action == "unwrap":
        unwrap_client_config(config_path)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

