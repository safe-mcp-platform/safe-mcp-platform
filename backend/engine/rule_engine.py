"""
Rule Execution Engine
Executes Python validation functions
"""

import importlib.util
from typing import Optional, Dict, Any
from pathlib import Path
import structlog

from utils.types import RuleResult
from config import settings

logger = structlog.get_logger()


class RuleEngine:
    """Executes rule validators dynamically."""
    
    def __init__(self):
        self.rule_cache = {}  # Cache loaded validators
    
    def execute(
        self,
        validator_path: str,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        """
        Execute a rule validator.
        
        Args:
            validator_path: Python path like "rules.T1102_rules.validate"
            input_text: Text to validate
            context: Additional context (e.g., user_id, session_id)
        
        Returns:
            RuleResult with validation outcome
        """
        try:
            validator_func = self._load_validator(validator_path)
            if not validator_func:
                return RuleResult(
                    triggered=False,
                    confidence=0.0,
                    reasons=["Validator not found"]
                )
            
            # Execute validator
            result = validator_func(input_text, context or {})
            
            # Validators should return RuleResult or dict
            if isinstance(result, RuleResult):
                return result
            elif isinstance(result, dict):
                return RuleResult(**result)
            else:
                logger.warning(f"Invalid validator return type: {type(result)}")
                return RuleResult(triggered=False, confidence=0.0)
                
        except Exception as e:
            logger.error(f"Rule execution failed: {validator_path}", error=str(e))
            return RuleResult(
                triggered=False,
                confidence=0.0,
                reasons=[f"Execution error: {str(e)}"]
            )
    
    def _load_validator(self, validator_path: str):
        """Load validator function dynamically."""
        if validator_path in self.rule_cache:
            return self.rule_cache[validator_path]
        
        try:
            # Parse path like "rules.T1102_rules.validate"
            parts = validator_path.split('.')
            module_path = '.'.join(parts[:-1])
            func_name = parts[-1]
            
            # Import module
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)
            
            # Cache it
            self.rule_cache[validator_path] = func
            logger.debug(f"Loaded validator: {validator_path}")
            
            return func
            
        except Exception as e:
            logger.error(f"Failed to load validator: {validator_path}", error=str(e))
            return None
    
    def clear_cache(self):
        """Clear validator cache."""
        self.rule_cache.clear()
        logger.debug("Rule cache cleared")


# Global instance
_rule_engine = None


def get_rule_engine() -> RuleEngine:
    """Get global rule engine instance."""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine

