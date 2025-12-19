"""
MCP Protocol Handler
Implements JSON-RPC 2.0 for Model Context Protocol
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class MCPMessage:
    """MCP JSON-RPC 2.0 Message"""
    jsonrpc: str = "2.0"
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMessage":
        """Parse JSON-RPC message from dict"""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data.get("method"),
            params=data.get("params"),
            id=data.get("id"),
            result=data.get("result"),
            error=data.get("error")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-RPC dict"""
        msg = {"jsonrpc": self.jsonrpc}
        
        if self.id is not None:
            msg["id"] = self.id
        
        if self.method:
            msg["method"] = self.method
            if self.params is not None:
                msg["params"] = self.params
        
        if self.result is not None:
            msg["result"] = self.result
        
        if self.error is not None:
            msg["error"] = self.error
        
        return msg
    
    def is_request(self) -> bool:
        """Check if this is a request message"""
        return self.method is not None
    
    def is_response(self) -> bool:
        """Check if this is a response message"""
        return self.result is not None or self.error is not None
    
    def is_notification(self) -> bool:
        """Check if this is a notification (request without id)"""
        return self.method is not None and self.id is None


class MCPProtocol:
    """MCP Protocol Handler"""
    
    # Standard MCP methods
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    COMPLETION_COMPLETE = "completion/complete"
    
    def __init__(self):
        self.initialized = False
        self.client_info: Optional[Dict[str, Any]] = None
    
    def parse_message(self, raw_message: str) -> MCPMessage:
        """Parse raw JSON-RPC message"""
        try:
            data = json.loads(raw_message)
            return MCPMessage.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse MCP message", error=str(e))
            raise ValueError(f"Invalid JSON-RPC message: {e}")
    
    def create_response(
        self,
        request_id: str,
        result: Any = None,
        error: Optional[Dict[str, Any]] = None
    ) -> MCPMessage:
        """Create response message"""
        return MCPMessage(
            id=request_id,
            result=result,
            error=error
        )
    
    def create_error_response(
        self,
        request_id: str,
        code: int,
        message: str,
        data: Optional[Any] = None
    ) -> MCPMessage:
        """Create error response"""
        error = {
            "code": code,
            "message": message
        }
        if data is not None:
            error["data"] = data
        
        return MCPMessage(
            id=request_id,
            error=error
        )
    
    def create_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> MCPMessage:
        """Create request message"""
        return MCPMessage(
            method=method,
            params=params,
            id=request_id
        )
    
    def serialize_message(self, message: MCPMessage) -> str:
        """Serialize message to JSON string"""
        return json.dumps(message.to_dict())
    
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        self.client_info = params
        self.initialized = True
        
        logger.info(
            "MCP client initialized",
            client_name=params.get("clientInfo", {}).get("name"),
            protocol_version=params.get("protocolVersion")
        )
        
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "safe-mcp-gateway",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": False},
                "prompts": {"listChanged": False},
                "logging": {}
            }
        }
    
    def validate_request(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Validate request and return error if invalid"""
        if not message.is_request():
            return self.create_error_response(
                message.id or "null",
                -32600,
                "Invalid Request",
                "Message is not a valid request"
            )
        
        if message.method != self.INITIALIZE and not self.initialized:
            return self.create_error_response(
                message.id,
                -32002,
                "Not Initialized",
                "Client must call initialize first"
            )
        
        return None


# Error codes (JSON-RPC 2.0 + MCP extensions)
class MCPErrorCode:
    """Standard JSON-RPC and MCP error codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific errors
    NOT_INITIALIZED = -32002
    UNKNOWN_ERROR_CODE = -32001
    REQUEST_TIMEOUT = -32000
    
    # SAFE-MCP security errors
    SECURITY_VIOLATION = -32000
    TECHNIQUE_BLOCKED = -32100
    SUSPICIOUS_PATTERN = -32101

