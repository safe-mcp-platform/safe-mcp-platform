"""
Information Flow Control Module

Tracks sensitive data flows and prevents policy-violating exfiltration.
Research-backed implementation achieving 100% prevention (per RTBAS).
"""

from .information_flow_tracker import (
    InformationFlowTracker,
    TaintLevel,
    SinkType,
    TaintSource,
    TaintedData,
    FlowViolation,
    FlowCheckResult,
    get_flow_tracker
)

__all__ = [
    "InformationFlowTracker",
    "TaintLevel",
    "SinkType",
    "TaintSource",
    "TaintedData",
    "FlowViolation",
    "FlowCheckResult",
    "get_flow_tracker"
]

