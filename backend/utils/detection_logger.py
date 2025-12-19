"""
Detection Logger
Logs detection results to database with MCP-specific fields
"""

from typing import Optional, Dict, Any
import structlog
from datetime import datetime

from database.connection import get_admin_db_session
from database.models import Detection
from utils.types import DetectionResult

logger = structlog.get_logger()


async def log_detection(
    result: DetectionResult,
    mcp_method: Optional[str] = None,
    mcp_tool_name: Optional[str] = None,
    mcp_tool_arguments: Optional[Dict[str, Any]] = None,
    mcp_server_name: Optional[str] = None
):
    """
    Log detection result to database with MCP-specific fields.
    
    Args:
        result: DetectionResult from detection engine
        mcp_method: MCP method (tools/call, resources/read, etc.)
        mcp_tool_name: MCP tool name (read_file, git_commit, etc.)
        mcp_tool_arguments: Tool arguments dict
        mcp_server_name: MCP server name (filesystem, git, etc.)
    """
    try:
        db = get_admin_db_session()
        
        # Extract pattern results
        patterns_matched = []
        if result.pattern_result and result.pattern_result.patterns_matched:
            patterns_matched = result.pattern_result.patterns_matched
        
        # Extract rule violations
        rules_violated = []
        if result.rule_result and result.rule_result.reasons:
            rules_violated = result.rule_result.reasons
        
        # Create detection record
        detection = Detection(
            request_id=result.request_id or f"det-{datetime.utcnow().timestamp()}",
            user_id=result.user_id,
            session_id=result.session_id,
            
            # Technique info
            technique_id=result.technique_id,
            technique_name=result.technique_name,
            input_text=result.input_text,
            
            # MCP-specific fields
            mcp_method=mcp_method,
            mcp_tool_name=mcp_tool_name,
            mcp_tool_arguments=mcp_tool_arguments,
            mcp_server_name=mcp_server_name,
            
            # Results
            blocked=result.blocked,
            confidence=result.confidence,
            risk_level=result.risk_level.value,
            
            # Method results
            pattern_triggered=result.pattern_result.triggered if result.pattern_result else False,
            pattern_confidence=result.pattern_result.confidence if result.pattern_result else 0.0,
            
            ml_triggered=result.ml_result.triggered if result.ml_result else False,
            ml_confidence=result.ml_result.confidence if result.ml_result else 0.0,
            
            rules_triggered=result.rule_result.triggered if result.rule_result else False,
            rules_confidence=result.rule_result.confidence if result.rule_result else 0.0,
            
            behavioral_triggered=result.behavioral_result.triggered if result.behavioral_result else False,
            behavioral_confidence=result.behavioral_result.confidence if result.behavioral_result else 0.0,
            
            # Evidence
            evidence=result.evidence,
            patterns_matched=patterns_matched,
            rules_violated=rules_violated,
            
            # Performance
            latency_ms=result.latency_ms
        )
        
        db.add(detection)
        db.commit()
        
        logger.info(
            "Detection logged",
            technique_id=result.technique_id,
            blocked=result.blocked,
            mcp_tool=mcp_tool_name
        )
        
    except Exception as e:
        logger.error("Failed to log detection", error=str(e))
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

