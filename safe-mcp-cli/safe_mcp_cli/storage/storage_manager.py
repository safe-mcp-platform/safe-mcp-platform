"""
Storage Manager - File-based storage for user configurations

Manages whitelists, user preferences, and local state.
Complements PostgreSQL (which handles audit logs and detections).

Directory Structure:
    ~/.safe-mcp/
    ├── whitelist.json              # Approved tools/servers
    ├── config.json                 # User preferences
    ├── protection_state.json       # Current protection status
    └── logs/                       # Local log cache
        └── 2025-12-17.log

Adopted from mcp-scan with enhancements.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import rich
from rich.console import Console

console = Console()


@dataclass
class WhitelistEntry:
    """An entry in the whitelist."""

    entity_type: str  # "tool", "server", "resource"
    name: str
    hash: str
    added_at: datetime
    added_by: str = "user"
    notes: str = ""


@dataclass
class ProtectionState:
    """Current protection state for a client."""

    client_name: str
    config_path: str
    protected: bool
    protected_at: Optional[datetime] = None
    gateway_url: str = "http://localhost:8002"
    detection_url: str = "http://localhost:8001"


@dataclass
class UserConfig:
    """User preferences."""

    default_gateway_url: str = "http://localhost:8002"
    default_detection_url: str = "http://localhost:8001"
    default_admin_url: str = "http://localhost:8000"
    enable_logging: bool = True
    enable_blocking: bool = True
    auto_update_whitelist: bool = False
    telemetry_enabled: bool = False


class StorageManager:
    """Manages file-based storage for safe-mcp CLI."""

    def __init__(self, storage_dir: str = "~/.safe-mcp"):
        """
        Initialize the storage manager.

        Args:
            storage_dir: Directory to store files (default: ~/.safe-mcp)
        """
        self.storage_dir = Path(os.path.expanduser(storage_dir))
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.whitelist_path = self.storage_dir / "whitelist.json"
        self.config_path = self.storage_dir / "config.json"
        self.protection_state_path = self.storage_dir / "protection_state.json"
        self.logs_dir = self.storage_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Load data
        self.whitelist: dict[str, WhitelistEntry] = self._load_whitelist()
        self.config: UserConfig = self._load_config()
        self.protection_states: dict[str, ProtectionState] = self._load_protection_states()

    # ========== Whitelist Management ==========

    def _load_whitelist(self) -> dict[str, WhitelistEntry]:
        """Load whitelist from disk."""
        if not self.whitelist_path.exists():
            return {}

        try:
            with open(self.whitelist_path, encoding="utf-8") as f:
                data = json.load(f)
                whitelist = {}
                for key, entry in data.items():
                    whitelist[key] = WhitelistEntry(
                        entity_type=entry["entity_type"],
                        name=entry["name"],
                        hash=entry["hash"],
                        added_at=datetime.fromisoformat(entry["added_at"]),
                        added_by=entry.get("added_by", "user"),
                        notes=entry.get("notes", ""),
                    )
                return whitelist
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to load whitelist: {e}[/yellow]")
            return {}

    def _save_whitelist(self) -> None:
        """Save whitelist to disk."""
        data = {}
        for key, entry in self.whitelist.items():
            data[key] = {
                "entity_type": entry.entity_type,
                "name": entry.name,
                "hash": entry.hash,
                "added_at": entry.added_at.isoformat(),
                "added_by": entry.added_by,
                "notes": entry.notes,
            }

        with open(self.whitelist_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_to_whitelist(
        self,
        entity_type: str,
        name: str,
        hash: str,
        notes: str = "",
    ) -> None:
        """
        Add an entry to the whitelist.

        Args:
            entity_type: Type of entity ("tool", "server", "resource")
            name: Name of the entity
            hash: Hash of the entity
            notes: Optional notes
        """
        key = f"{entity_type}.{name}"
        self.whitelist[key] = WhitelistEntry(
            entity_type=entity_type,
            name=name,
            hash=hash,
            added_at=datetime.now(),
            added_by="user",
            notes=notes,
        )
        self._save_whitelist()
        console.print(f"[green]✓[/green] Added to whitelist: {key}")

    def remove_from_whitelist(self, entity_type: str, name: str) -> bool:
        """
        Remove an entry from the whitelist.

        Args:
            entity_type: Type of entity
            name: Name of the entity

        Returns:
            True if removed, False if not found
        """
        key = f"{entity_type}.{name}"
        if key in self.whitelist:
            del self.whitelist[key]
            self._save_whitelist()
            console.print(f"[green]✓[/green] Removed from whitelist: {key}")
            return True
        else:
            console.print(f"[yellow]⚠️  Not in whitelist: {key}[/yellow]")
            return False

    def is_whitelisted(self, entity_type: str, name: str, hash: str) -> bool:
        """
        Check if an entity is whitelisted.

        Args:
            entity_type: Type of entity
            name: Name of the entity
            hash: Hash of the entity

        Returns:
            True if whitelisted with matching hash
        """
        key = f"{entity_type}.{name}"
        if key in self.whitelist:
            return self.whitelist[key].hash == hash
        return False

    def get_whitelist(self) -> list[WhitelistEntry]:
        """Get all whitelist entries."""
        return list(self.whitelist.values())

    def clear_whitelist(self) -> None:
        """Clear all whitelist entries."""
        self.whitelist = {}
        self._save_whitelist()
        console.print("[green]✓[/green] Whitelist cleared")

    # ========== Config Management ==========

    def _load_config(self) -> UserConfig:
        """Load user config from disk."""
        if not self.config_path.exists():
            # Create default config
            config = UserConfig()
            self._save_config(config)
            return config

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
                return UserConfig(**data)
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to load config: {e}[/yellow]")
            return UserConfig()

    def _save_config(self, config: Optional[UserConfig] = None) -> None:
        """Save user config to disk."""
        if config is None:
            config = self.config

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config.__dict__, f, indent=2)

    def update_config(self, **kwargs: Any) -> None:
        """
        Update user config.

        Args:
            **kwargs: Config keys to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self._save_config()
        console.print("[green]✓[/green] Config updated")

    def get_config(self) -> UserConfig:
        """Get current user config."""
        return self.config

    # ========== Protection State Management ==========

    def _load_protection_states(self) -> dict[str, ProtectionState]:
        """Load protection states from disk."""
        if not self.protection_state_path.exists():
            return {}

        try:
            with open(self.protection_state_path, encoding="utf-8") as f:
                data = json.load(f)
                states = {}
                for client_name, state_data in data.items():
                    states[client_name] = ProtectionState(
                        client_name=state_data["client_name"],
                        config_path=state_data["config_path"],
                        protected=state_data["protected"],
                        protected_at=(
                            datetime.fromisoformat(state_data["protected_at"])
                            if state_data.get("protected_at")
                            else None
                        ),
                        gateway_url=state_data.get("gateway_url", "http://localhost:8002"),
                        detection_url=state_data.get("detection_url", "http://localhost:8001"),
                    )
                return states
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to load protection states: {e}[/yellow]")
            return {}

    def _save_protection_states(self) -> None:
        """Save protection states to disk."""
        data = {}
        for client_name, state in self.protection_states.items():
            data[client_name] = {
                "client_name": state.client_name,
                "config_path": state.config_path,
                "protected": state.protected,
                "protected_at": state.protected_at.isoformat() if state.protected_at else None,
                "gateway_url": state.gateway_url,
                "detection_url": state.detection_url,
            }

        with open(self.protection_state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def set_protected(
        self,
        client_name: str,
        config_path: str,
        gateway_url: str,
        detection_url: str,
    ) -> None:
        """
        Mark a client as protected.

        Args:
            client_name: Name of the client
            config_path: Path to config file
            gateway_url: Gateway URL
            detection_url: Detection API URL
        """
        self.protection_states[client_name] = ProtectionState(
            client_name=client_name,
            config_path=config_path,
            protected=True,
            protected_at=datetime.now(),
            gateway_url=gateway_url,
            detection_url=detection_url,
        )
        self._save_protection_states()

    def set_unprotected(self, client_name: str) -> None:
        """
        Mark a client as unprotected.

        Args:
            client_name: Name of the client
        """
        if client_name in self.protection_states:
            self.protection_states[client_name].protected = False
            self._save_protection_states()

    def is_protected(self, client_name: str) -> bool:
        """
        Check if a client is protected.

        Args:
            client_name: Name of the client

        Returns:
            True if protected
        """
        if client_name in self.protection_states:
            return self.protection_states[client_name].protected
        return False

    def get_protection_state(self, client_name: str) -> Optional[ProtectionState]:
        """
        Get protection state for a client.

        Args:
            client_name: Name of the client

        Returns:
            ProtectionState if found, None otherwise
        """
        return self.protection_states.get(client_name)

    # ========== Logging ==========

    def log_event(self, event_type: str, message: str, metadata: Optional[dict] = None) -> None:
        """
        Log an event to local log file.

        Args:
            event_type: Type of event ("protection", "detection", "error", etc.)
            message: Log message
            metadata: Optional metadata
        """
        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")


# Global instance
_storage_manager: Optional[StorageManager] = None


def get_storage() -> StorageManager:
    """Get the global storage manager instance."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager


if __name__ == "__main__":
    # Test the storage manager
    storage = StorageManager()

    # Test whitelist
    storage.add_to_whitelist("tool", "read_file", "abc123", "Safe tool")
    storage.add_to_whitelist("server", "filesystem", "def456", "Trusted server")

    print("\n📋 Whitelist:")
    for entry in storage.get_whitelist():
        print(f"  {entry.entity_type}.{entry.name}: {entry.hash}")

    # Test config
    storage.update_config(enable_blocking=False, telemetry_enabled=True)
    print(f"\n⚙️  Config: {storage.get_config()}")

    # Test protection state
    storage.set_protected("cursor", "~/.cursor/mcp.json", "http://localhost:8002", "http://localhost:8001")
    print(f"\n🛡️  Protection State: {storage.get_protection_state('cursor')}")

    # Test logging
    storage.log_event("test", "Test log message", {"foo": "bar"})
    print(f"\n📝 Log written to: {storage.logs_dir}")

