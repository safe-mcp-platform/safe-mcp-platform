"""
Configuration Loader
Loads technique configurations from JSON files
"""

import json
import os
from typing import Dict, Optional
from pathlib import Path
import structlog

from utils.types import TechniqueConfig
from config import settings

logger = structlog.get_logger()


class ConfigLoader:
    """Loads and manages technique configurations."""
    
    def __init__(self):
        self.techniques: Dict[str, TechniqueConfig] = {}
        self.patterns_cache: Dict[str, list] = {}
        self._load_all_techniques()
    
    def _load_all_techniques(self):
        """Load all technique configurations from disk."""
        techniques_dir = Path(settings.TECHNIQUES_DIR)
        
        if not techniques_dir.exists():
            logger.warning(f"Techniques directory not found: {techniques_dir}")
            return
        
        # Load all JSON files
        for json_file in techniques_dir.glob("T*.json"):
            try:
                self._load_technique(json_file)
            except Exception as e:
                logger.error(f"Failed to load technique: {json_file}", error=str(e))
        
        logger.info(f"Loaded {len(self.techniques)} technique configurations")
    
    def _load_technique(self, json_path: Path):
        """Load a single technique configuration."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        technique_id = data.get("id")
        if not technique_id:
            logger.warning(f"Technique missing ID: {json_path}")
            return
        
        # Parse into Pydantic model
        config = TechniqueConfig(**data)
        
        # Load patterns if configured
        if config.detection.patterns and config.detection.patterns.get("enabled"):
            pattern_file = config.detection.patterns.get("file")
            if pattern_file:
                self._load_patterns(technique_id, pattern_file)
        
        self.techniques[technique_id] = config
        logger.debug(f"Loaded technique: {technique_id} - {config.name}")
    
    def _load_patterns(self, technique_id: str, pattern_file: str):
        """Load regex patterns from file."""
        patterns_path = Path(settings.PATTERNS_DIR) / Path(pattern_file).name
        
        if not patterns_path.exists():
            logger.warning(f"Pattern file not found: {patterns_path}")
            return
        
        patterns = []
        with open(patterns_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    patterns.append(line)
        
        self.patterns_cache[technique_id] = patterns
        logger.debug(f"Loaded {len(patterns)} patterns for {technique_id}")
    
    def get_technique(self, technique_id: str) -> Optional[TechniqueConfig]:
        """Get technique configuration by ID."""
        return self.techniques.get(technique_id)
    
    def get_patterns(self, technique_id: str) -> list:
        """Get patterns for a technique."""
        return self.patterns_cache.get(technique_id, [])
    
    def get_all_techniques(self) -> Dict[str, TechniqueConfig]:
        """Get all loaded techniques."""
        return self.techniques
    
    def list_techniques(self) -> list:
        """Get all loaded techniques as a list."""
        return list(self.techniques.values())
    
    def reload(self):
        """Reload all configurations (for hot-reload)."""
        self.techniques.clear()
        self.patterns_cache.clear()
        self._load_all_techniques()
        logger.info("Configuration reloaded")


# Global instance
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """Get global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

