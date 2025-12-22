"""
Execution Isolation Module

Provides capability-based sandboxing and least-privilege enforcement for MCP tools.
Research-backed implementation addressing critical security gaps.
"""

from .execution_isolation import (
    ExecutionIsolation,
    IsolationPolicy,
    IsolationResult,
    ToolCapability,
    get_isolation_layer
)

__all__ = [
    "ExecutionIsolation",
    "IsolationPolicy",
    "IsolationResult",
    "ToolCapability",
    "get_isolation_layer"
]

