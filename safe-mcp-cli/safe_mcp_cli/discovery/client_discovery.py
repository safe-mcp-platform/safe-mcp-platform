"""
MCP Client Auto-Discovery

Automatically discovers MCP configurations from well-known clients:
- Claude Desktop
- Cursor
- Windsurf
- VSCode
- Cline

Adopted from mcp-scan by Invariant Labs with enhancements.
"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import rich
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

console = Console()


@dataclass
class ClientInfo:
    """Information about an MCP client."""

    name: str
    display_name: str
    config_paths: list[str]
    description: str
    icon: str


# Well-known MCP clients and their configuration paths
def get_client_definitions() -> dict[str, ClientInfo]:
    """Get client definitions based on the current platform."""
    platform = sys.platform

    if platform == "darwin":  # macOS
        return {
            "claude": ClientInfo(
                name="claude",
                display_name="Claude Desktop",
                config_paths=["~/Library/Application Support/Claude/claude_desktop_config.json"],
                description="Anthropic's Claude AI assistant",
                icon="🤖",
            ),
            "cursor": ClientInfo(
                name="cursor",
                display_name="Cursor IDE",
                config_paths=["~/.cursor/mcp.json"],
                description="AI-powered code editor",
                icon="💻",
            ),
            "windsurf": ClientInfo(
                name="windsurf",
                display_name="Windsurf IDE",
                config_paths=["~/.codeium/windsurf/mcp_config.json"],
                description="Codeium's AI development environment",
                icon="🏄",
            ),
            "vscode": ClientInfo(
                name="vscode",
                display_name="VS Code",
                config_paths=[
                    "~/Library/Application Support/Code/User/settings.json",
                    "~/Library/Application Support/Code/User/mcp.json",
                    "~/.vscode/mcp.json",
                ],
                description="Microsoft Visual Studio Code",
                icon="📝",
            ),
            "cline": ClientInfo(
                name="cline",
                display_name="Cline",
                config_paths=["~/.cline/mcp.json"],
                description="Command-line MCP client",
                icon="⚡",
            ),
        }
    elif platform in ("linux", "linux2"):  # Linux
        return {
            "cursor": ClientInfo(
                name="cursor",
                display_name="Cursor IDE",
                config_paths=["~/.cursor/mcp.json"],
                description="AI-powered code editor",
                icon="💻",
            ),
            "windsurf": ClientInfo(
                name="windsurf",
                display_name="Windsurf IDE",
                config_paths=["~/.codeium/windsurf/mcp_config.json"],
                description="Codeium's AI development environment",
                icon="🏄",
            ),
            "vscode": ClientInfo(
                name="vscode",
                display_name="VS Code",
                config_paths=[
                    "~/.config/Code/User/settings.json",
                    "~/.config/Code/User/mcp.json",
                    "~/.vscode/mcp.json",
                ],
                description="Microsoft Visual Studio Code",
                icon="📝",
            ),
            "cline": ClientInfo(
                name="cline",
                display_name="Cline",
                config_paths=["~/.cline/mcp.json"],
                description="Command-line MCP client",
                icon="⚡",
            ),
        }
    elif platform == "win32":  # Windows
        return {
            "claude": ClientInfo(
                name="claude",
                display_name="Claude Desktop",
                config_paths=["~/AppData/Roaming/Claude/claude_desktop_config.json"],
                description="Anthropic's Claude AI assistant",
                icon="🤖",
            ),
            "cursor": ClientInfo(
                name="cursor",
                display_name="Cursor IDE",
                config_paths=["~/.cursor/mcp.json"],
                description="AI-powered code editor",
                icon="💻",
            ),
            "windsurf": ClientInfo(
                name="windsurf",
                display_name="Windsurf IDE",
                config_paths=["~/.codeium/windsurf/mcp_config.json"],
                description="Codeium's AI development environment",
                icon="🏄",
            ),
            "vscode": ClientInfo(
                name="vscode",
                display_name="VS Code",
                config_paths=[
                    "~/AppData/Roaming/Code/User/settings.json",
                    "~/AppData/Roaming/Code/User/mcp.json",
                    "~/.vscode/mcp.json",
                ],
                description="Microsoft Visual Studio Code",
                icon="📝",
            ),
            "cline": ClientInfo(
                name="cline",
                display_name="Cline",
                config_paths=["~/.cline/mcp.json"],
                description="Command-line MCP client",
                icon="⚡",
            ),
        }
    else:
        return {}


@dataclass
class DiscoveredConfig:
    """A discovered MCP configuration file."""

    client: ClientInfo
    config_path: str
    exists: bool
    server_count: int
    servers: list[str]
    error: Optional[str] = None


def parse_mcp_config(config_path: str) -> tuple[list[str], Optional[str]]:
    """
    Parse an MCP config file and return server names.

    Args:
        config_path: Path to the config file

    Returns:
        Tuple of (server_names, error_message)
    """
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        # Handle different config formats
        if "mcpServers" in data:
            servers = list(data["mcpServers"].keys())
        elif "mcp" in data and isinstance(data["mcp"], dict) and "servers" in data["mcp"]:
            # VSCode settings.json format
            servers = list(data["mcp"]["servers"].keys())
        else:
            return [], "Unknown config format"

        return servers, None
    except json.JSONDecodeError as e:
        return [], f"Invalid JSON: {e}"
    except Exception as e:
        return [], f"Error reading config: {e}"


def discover_all_configs(verbose: bool = False) -> list[DiscoveredConfig]:
    """
    Discover all MCP configurations on the system.

    Args:
        verbose: Print detailed information during discovery

    Returns:
        List of discovered configurations
    """
    discovered = []
    clients = get_client_definitions()

    if verbose:
        console.print("\n[bold cyan]🔍 Scanning for MCP clients...[/bold cyan]\n")

    for client_info in clients.values():
        for config_path in client_info.config_paths:
            expanded_path = os.path.expanduser(config_path)

            if os.path.exists(expanded_path):
                if verbose:
                    console.print(f"  [green]✓[/green] Found: {config_path}")

                servers, error = parse_mcp_config(expanded_path)
                discovered.append(
                    DiscoveredConfig(
                        client=client_info,
                        config_path=expanded_path,
                        exists=True,
                        server_count=len(servers),
                        servers=servers,
                        error=error,
                    )
                )
            else:
                if verbose:
                    console.print(f"  [dim]✗[/dim] Not found: {config_path}")

    return discovered


def display_discovered_configs(discovered: list[DiscoveredConfig], show_details: bool = False) -> None:
    """
    Display discovered configurations in a rich table.

    Args:
        discovered: List of discovered configs
        show_details: Show detailed server information
    """
    if not discovered:
        console.print("\n[yellow]⚠️  No MCP configurations found on this system.[/yellow]")
        console.print("\n[dim]Searched for: Claude Desktop, Cursor, Windsurf, VS Code, Cline[/dim]\n")
        return

    table = Table(title="\n🎯 Discovered MCP Configurations", show_header=True, header_style="bold cyan")
    table.add_column("Client", style="cyan", no_wrap=True)
    table.add_column("Config Path", style="white")
    table.add_column("Servers", justify="center", style="green")
    table.add_column("Status", justify="center")

    for config in discovered:
        status = "✅ Ready" if config.server_count > 0 else "⚠️  Empty"
        if config.error:
            status = "❌ Error"

        table.add_row(
            f"{config.client.icon} {config.client.display_name}",
            config.config_path,
            str(config.server_count),
            status,
        )

    console.print(table)

    if show_details:
        console.print("\n[bold]📋 Server Details:[/bold]\n")
        for config in discovered:
            if config.servers:
                tree = Tree(f"{config.client.icon} {config.client.display_name}")
                for server in config.servers:
                    tree.add(f"[cyan]{server}[/cyan]")
                console.print(tree)

    console.print()


def get_client_by_name(client_name: str) -> Optional[DiscoveredConfig]:
    """
    Get a specific client's configuration.

    Args:
        client_name: Name of the client (e.g., 'cursor', 'claude')

    Returns:
        DiscoveredConfig if found, None otherwise
    """
    discovered = discover_all_configs()
    for config in discovered:
        if config.client.name == client_name.lower():
            return config
    return None


def get_all_config_paths() -> list[str]:
    """Get all possible MCP config paths for the current platform."""
    clients = get_client_definitions()
    paths = []
    for client in clients.values():
        paths.extend(client.config_paths)
    return paths


if __name__ == "__main__":
    # Test the discovery
    rich.print("\n[bold cyan]🔍 MCP Client Discovery Test[/bold cyan]\n")
    configs = discover_all_configs(verbose=True)
    display_discovered_configs(configs, show_details=True)

