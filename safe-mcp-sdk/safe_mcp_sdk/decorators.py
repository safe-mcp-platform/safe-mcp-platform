"""
The @secure decorator - 1-line security for MCP tools
"""

from functools import wraps
from typing import List, Optional, Callable
import inspect
import logging
from datetime import datetime

from .validators import SAFEMCPValidator
from .exceptions import SAFEMCPException

# Global validator instance
_validator = SAFEMCPValidator()

# Setup logging
logger = logging.getLogger("safe_mcp_sdk")
logger.setLevel(logging.INFO)

def secure(
    techniques: Optional[List[str]] = None,
    block: bool = True,
    log: bool = True
):
    """
    Decorator to secure MCP tool functions with SAFE-MCP techniques.
    
    Usage:
        @server.tool()
        @secure()  # Applies all SAFE-MCP techniques
        async def my_tool(input: str):
            return process(input)
        
        @server.tool()
        @secure(techniques=["SAFE-T1102", "SAFE-T1105"])  # Specific techniques
        async def sensitive_tool(data: str):
            return process(data)
    
    Args:
        techniques: List of technique IDs to check, or None for all
        block: If True, raises exception on detection. If False, only logs warning.
        log: If True, logs security events
    """
    
    def decorator(func: Callable):
        # Get function signature
        sig = inspect.signature(func)
        func_name = func.__name__
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract arguments
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each string input
            for param_name, param_value in bound_args.arguments.items():
                if not isinstance(param_value, str):
                    continue
                
                # Validate against SAFE-MCP techniques
                result = _validator.validate(
                    input_text=param_value,
                    techniques=techniques,
                    context={
                        "function": func_name,
                        "parameter": param_name,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                if result.get("blocked"):
                    # Security violation detected!
                    if log:
                        logger.warning(
                            f"🚨 Security violation in {func_name}({param_name}): "
                            f"{result['technique_id']} - {result['message']}"
                        )
                    
                    if block:
                        # Raise exception to block execution
                        raise SAFEMCPException(
                            technique_id=result["technique_id"],
                            message=result["message"],
                            severity=result["severity"],
                            evidence=result["evidence"],
                            parameter=param_name
                        )
                    else:
                        # Warn only
                        import warnings
                        warnings.warn(
                            f"Security warning in {func_name}: {result['message']}"
                        )
            
            # All validations passed - execute function
            if log:
                logger.info(f"✅ {func_name} - Security validation passed")
            
            return await func(*args, **kwargs)
        
        # Attach metadata
        wrapper.__secure__ = True
        wrapper.__techniques__ = techniques or "all"
        
        return wrapper
    
    return decorator

