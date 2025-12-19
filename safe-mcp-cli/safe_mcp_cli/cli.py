#!/usr/bin/env python3
"""
SAFE-MCP CLI - Professional Command-Line Interface

Professional CLI for protecting MCP deployments with transparent runtime security.

Commands:
- scan: Discover MCP configurations on your system
- protect: Enable runtime protection for a client
- unprotect: Disable runtime protection
- status: Show protection status
- logs: View security logs
- dashboard: Launch admin dashboard

Example Usage:
    safe-mcp scan                    # Discover all MCP clients
    safe-mcp protect cursor          # Protect Cursor IDE
    safe-mcp protect --all           # Protect all clients
    safe-mcp unprotect cursor        # Remove protection
    safe-mcp status                  # Check what's protected
    safe-mcp logs --tail 50          # View recent logs
    safe-mcp dashboard               # Open admin UI
"""

import argparse
import sys
import webbrowser
from typing import Optional

import rich
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from safe_mcp_cli.discovery.client_discovery import (
    discover_all_configs,
    display_discovered_configs,
    get_client_by_name,
)
from safe_mcp_cli.gateway.config_injector import (
    InjectionConfig,
    unwrap_client_config,
    wrap_client_config,
)

console = Console()


def cmd_scan(args: argparse.Namespace) -> int:
    """
    Scan for MCP configurations on the system.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success)
    """
    console.print("\n[bold cyan]🔍 Scanning for MCP Clients...[/bold cyan]\n")

    discovered = discover_all_configs(verbose=args.verbose)
    display_discovered_configs(discovered, show_details=args.details)

    if discovered:
        console.print(
            Panel(
                f"[green]✅ Found {len(discovered)} MCP configuration(s)[/green]\n\n"
                f"[dim]To enable protection:[/dim]\n"
                f"  [cyan]safe-mcp protect <client-name>[/cyan]\n"
                f"  [cyan]safe-mcp protect --all[/cyan]\n\n"
                f"[dim]Example:[/dim]\n"
                f"  [cyan]safe-mcp protect cursor[/cyan]",
                title="📋 Next Steps",
                border_style="cyan",
            )
        )
        return 0
    else:
        console.print(
            Panel(
                "[yellow]⚠️  No MCP configurations found[/yellow]\n\n"
                "[dim]Searched for: Claude Desktop, Cursor, Windsurf, VS Code, Cline[/dim]\n\n"
                "[dim]If you have one of these clients installed, make sure you have configured MCP servers.[/dim]",
                title="🔍 Discovery Complete",
                border_style="yellow",
            )
        )
        return 1


def cmd_protect(args: argparse.Namespace) -> int:
    """
    Enable runtime protection for MCP client(s).

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success)
    """
    injection_config = InjectionConfig(
        gateway_url=args.gateway_url,
        detection_url=args.detection_url,
        admin_url=args.admin_url,
        enable_logging=not args.no_logging,
        enable_blocking=not args.no_blocking,
    )

    if args.all:
        # Protect all discovered clients
        console.print("\n[bold cyan]🛡️  Protecting All MCP Clients...[/bold cyan]\n")
        discovered = discover_all_configs()

        if not discovered:
            console.print("[yellow]⚠️  No MCP configurations found to protect[/yellow]")
            return 1

        success_count = 0
        for config in discovered:
            console.print(f"\n[bold]Processing: {config.client.display_name}[/bold]")
            if wrap_client_config(config.config_path, injection_config, verbose=not args.quiet):
                success_count += 1

        console.print(f"\n[green]✅ Protected {success_count}/{len(discovered)} clients[/green]\n")
        return 0 if success_count > 0 else 1

    elif args.client:
        # Protect specific client
        client_name = args.client.lower()
        config = get_client_by_name(client_name)

        if not config:
            console.print(f"[red]✗[/red] Client '{args.client}' not found\n")
            console.print("[dim]Run 'safe-mcp scan' to see available clients[/dim]\n")
            return 1

        return 0 if wrap_client_config(config.config_path, injection_config, verbose=not args.quiet) else 1

    elif args.config:
        # Protect custom config path
        return 0 if wrap_client_config(args.config, injection_config, verbose=not args.quiet) else 1

    else:
        console.print("[red]✗[/red] Please specify --client, --config, or --all\n")
        return 1


def cmd_unprotect(args: argparse.Namespace) -> int:
    """
    Disable runtime protection for MCP client(s).

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success)
    """
    if args.all:
        # Unprotect all discovered clients
        console.print("\n[bold cyan]🔓 Removing Protection from All MCP Clients...[/bold cyan]\n")
        discovered = discover_all_configs()

        if not discovered:
            console.print("[yellow]⚠️  No MCP configurations found[/yellow]")
            return 1

        success_count = 0
        for config in discovered:
            console.print(f"\n[bold]Processing: {config.client.display_name}[/bold]")
            if unwrap_client_config(config.config_path, verbose=not args.quiet):
                success_count += 1

        console.print(f"\n[green]✅ Unprotected {success_count}/{len(discovered)} clients[/green]\n")
        return 0 if success_count > 0 else 1

    elif args.client:
        # Unprotect specific client
        client_name = args.client.lower()
        config = get_client_by_name(client_name)

        if not config:
            console.print(f"[red]✗[/red] Client '{args.client}' not found\n")
            console.print("[dim]Run 'safe-mcp scan' to see available clients[/dim]\n")
            return 1

        return 0 if unwrap_client_config(config.config_path, verbose=not args.quiet) else 1

    elif args.config:
        # Unprotect custom config path
        return 0 if unwrap_client_config(args.config, verbose=not args.quiet) else 1

    else:
        console.print("[red]✗[/red] Please specify --client, --config, or --all\n")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """
    Show protection status for all MCP clients.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success)
    """
    console.print("\n[bold cyan]📊 Protection Status[/bold cyan]\n")

    discovered = discover_all_configs()

    if not discovered:
        console.print("[yellow]⚠️  No MCP configurations found[/yellow]\n")
        return 1

    table = Table(title="MCP Client Protection Status", show_header=True, header_style="bold cyan")
    table.add_column("Client", style="cyan", no_wrap=True)
    table.add_column("Config Path", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Servers", justify="center")

    from safe_mcp_cli.gateway.config_injector import MCPConfigInjector

    protected_count = 0

    for config in discovered:
        injector = MCPConfigInjector(config.config_path)
        is_protected = injector.is_wrapped()

        if is_protected:
            status = "[green]🛡️  Protected[/green]"
            protected_count += 1
        else:
            status = "[red]❌ Unprotected[/red]"

        table.add_row(
            f"{config.client.icon} {config.client.display_name}",
            config.config_path,
            status,
            str(config.server_count),
        )

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {protected_count}/{len(discovered)} clients protected\n")

    if protected_count < len(discovered):
        console.print(
            Panel(
                "[yellow]⚠️  Some clients are unprotected[/yellow]\n\n"
                "[dim]To enable protection:[/dim]\n"
                "  [cyan]safe-mcp protect <client-name>[/cyan]\n"
                "  [cyan]safe-mcp protect --all[/cyan]",
                title="💡 Recommendation",
                border_style="yellow",
            )
        )

    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    """
    View security logs.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success)
    """
    console.print("\n[bold cyan]📋 Security Logs[/bold cyan]\n")
    console.print("[yellow]⚠️  Log viewing not yet implemented[/yellow]")
    console.print("[dim]Coming soon: Real-time log streaming from PostgreSQL[/dim]\n")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    """
    Launch the admin dashboard.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success)
    """
    dashboard_url = args.url

    console.print(f"\n[bold cyan]🚀 Launching Admin Dashboard...[/bold cyan]\n")
    console.print(f"[dim]URL: {dashboard_url}[/dim]\n")

    try:
        webbrowser.open(dashboard_url)
        console.print("[green]✓[/green] Dashboard opened in your browser\n")
        return 0
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to open dashboard: {e}\n")
        console.print(f"[dim]Please open manually: {dashboard_url}[/dim]\n")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="safe-mcp",
        description="Professional CLI for securing Model Context Protocol deployments",
        epilog="For more information, visit: https://github.com/safe-mcp-platform/safe-mcp-platform",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="safe-mcp 1.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Discover MCP configurations on your system")
    scan_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    scan_parser.add_argument("--details", "-d", action="store_true", help="Show detailed server information")
    scan_parser.set_defaults(func=cmd_scan)

    # protect command
    protect_parser = subparsers.add_parser("protect", help="Enable runtime protection for MCP client(s)")
    protect_parser.add_argument("--client", "-c", type=str, help="Client name (cursor, claude, windsurf, etc.)")
    protect_parser.add_argument("--config", type=str, help="Custom config file path")
    protect_parser.add_argument("--all", "-a", action="store_true", help="Protect all discovered clients")
    protect_parser.add_argument("--gateway-url", default="http://localhost:8002", help="Gateway URL")
    protect_parser.add_argument("--detection-url", default="http://localhost:8001", help="Detection API URL")
    protect_parser.add_argument("--admin-url", default="http://localhost:8000", help="Admin dashboard URL")
    protect_parser.add_argument("--no-logging", action="store_true", help="Disable request logging")
    protect_parser.add_argument("--no-blocking", action="store_true", help="Log only (don't block threats)")
    protect_parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    protect_parser.set_defaults(func=cmd_protect)

    # unprotect command
    unprotect_parser = subparsers.add_parser("unprotect", help="Disable runtime protection")
    unprotect_parser.add_argument("--client", "-c", type=str, help="Client name")
    unprotect_parser.add_argument("--config", type=str, help="Custom config file path")
    unprotect_parser.add_argument("--all", "-a", action="store_true", help="Unprotect all clients")
    unprotect_parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    unprotect_parser.set_defaults(func=cmd_unprotect)

    # status command
    status_parser = subparsers.add_parser("status", help="Show protection status for all clients")
    status_parser.set_defaults(func=cmd_status)

    # logs command
    logs_parser = subparsers.add_parser("logs", help="View security logs")
    logs_parser.add_argument("--tail", "-n", type=int, default=50, help="Number of recent logs to show")
    logs_parser.add_argument("--follow", "-f", action="store_true", help="Follow log output in real-time")
    logs_parser.add_argument("--filter", type=str, help="Filter logs by keyword")
    logs_parser.set_defaults(func=cmd_logs)

    # dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Launch admin dashboard")
    dashboard_parser.add_argument("--url", default="http://localhost:8000", help="Dashboard URL")
    dashboard_parser.set_defaults(func=cmd_dashboard)

    # Parse args
    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        console.print(
            "\n[bold cyan]Quick Start:[/bold cyan]\n"
            "  1. [cyan]safe-mcp scan[/cyan]                 # Discover MCP clients\n"
            "  2. [cyan]safe-mcp protect cursor[/cyan]       # Enable protection\n"
            "  3. [cyan]safe-mcp status[/cyan]               # Check status\n"
            "  4. [cyan]safe-mcp dashboard[/cyan]            # Open admin UI\n"
        )
        return 1

    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Operation cancelled by user[/yellow]\n")
        return 130
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}\n")
        if args.command in vars(args) and vars(args).get("verbose"):
            import traceback

            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        return 1


if __name__ == "__main__":
    sys.exit(main())

