"""
MCP Protocol Parser - JSON-RPC 2.0 Message Parser for Model Context Protocol

Parses and validates MCP protocol messages according to the specification.
MCP uses JSON-RPC 2.0 as its base protocol.

Specification: https://modelcontextprotocol.io/docs/specification/protocol
"""
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class MCPMessageType(Enum):
    """MCP message types"""
    # Requests
    INITIALIZE = "initialize"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    SAMPLING_CREATE_MESSAGE = "sampling/createMessage"
    
    # Notifications
    NOTIFICATIONS_CANCELLED = "notifications/cancelled"
    NOTIFICATIONS_PROGRESS = "notifications/progress"
    NOTIFICATIONS_MESSAGE = "notifications/message"
    NOTIFICATIONS_RESOURCES_UPDATED = "notifications/resources/updated"
    
    # Responses
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class MCPMessage:
    """
    Parsed MCP protocol message.
    
    Based on JSON-RPC 2.0 specification with MCP extensions.
    """
    # JSON-RPC 2.0 fields
    jsonrpc: str  # Always "2.0"
    method: Optional[str] = None  # For requests
    params: Optional[Dict[str, Any]] = None  # Request parameters
    id: Optional[Union[str, int]] = None  # Request/Response ID
    
    # Response fields
    result: Optional[Any] = None  # For successful responses
    error: Optional[Dict[str, Any]] = None  # For error responses
    
    # MCP-specific parsed data
    message_type: Optional[MCPMessageType] = None
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    resource_uri: Optional[str] = None
    
    # Raw message
    raw: Dict[str, Any] = field(default_factory=dict)
    
    def is_request(self) -> bool:
        """Check if this is a request message"""
        return self.method is not None and self.id is not None
    
    def is_notification(self) -> bool:
        """Check if this is a notification (request without ID)"""
        return self.method is not None and self.id is None
    
    def is_response(self) -> bool:
        """Check if this is a response message"""
        return self.id is not None and self.method is None
    
    def is_tool_call(self) -> bool:
        """Check if this is a tool call request"""
        return self.method == "tools/call"
    
    def is_resource_read(self) -> bool:
        """Check if this is a resource read request"""
        return self.method == "resources/read"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert back to dict format"""
        msg = {"jsonrpc": self.jsonrpc}
        
        if self.method:
            msg["method"] = self.method
        
        if self.params is not None:
            msg["params"] = self.params
        
        if self.id is not None:
            msg["id"] = self.id
        
        if self.result is not None:
            msg["result"] = self.result
        
        if self.error is not None:
            msg["error"] = self.error
        
        return msg


class MCPProtocolParser:
    """
    Parser for MCP protocol messages.
    
    Handles:
    - JSON-RPC 2.0 validation
    - MCP-specific message types
    - Tool call extraction
    - Resource URI parsing
    """
    
    @staticmethod
    def parse(raw_message: Dict[str, Any]) -> MCPMessage:
        """
        Parse a raw MCP message into structured format.
        
        Args:
            raw_message: Raw JSON-RPC 2.0 message
        
        Returns:
            MCPMessage object with parsed fields
        
        Raises:
            ValueError: If message is invalid
        """
        # Validate JSON-RPC 2.0 format
        if not isinstance(raw_message, dict):
            raise ValueError("Message must be a dictionary")
        
        if raw_message.get("jsonrpc") != "2.0":
            raise ValueError("Invalid JSON-RPC version (must be 2.0)")
        
        # Extract basic fields
        message = MCPMessage(
            jsonrpc=raw_message["jsonrpc"],
            method=raw_message.get("method"),
            params=raw_message.get("params"),
            id=raw_message.get("id"),
            result=raw_message.get("result"),
            error=raw_message.get("error"),
            raw=raw_message
        )
        
        # Determine message type
        if message.method:
            try:
                message.message_type = MCPMessageType(message.method)
            except ValueError:
                # Unknown method, keep as string
                pass
        
        # Parse MCP-specific fields
        if message.is_tool_call():
            message.tool_name, message.tool_arguments = MCPProtocolParser._parse_tool_call(message)
        
        elif message.is_resource_read():
            message.resource_uri = MCPProtocolParser._parse_resource_read(message)
        
        return message
    
    @staticmethod
    def _parse_tool_call(message: MCPMessage) -> tuple:
        """Extract tool name and arguments from tools/call request"""
        params = message.params or {}
        tool_name = params.get("name", "")
        tool_arguments = params.get("arguments", {})
        return tool_name, tool_arguments
    
    @staticmethod
    def _parse_resource_read(message: MCPMessage) -> str:
        """Extract resource URI from resources/read request"""
        params = message.params or {}
        return params.get("uri", "")
    
    @staticmethod
    def create_tool_call(
        tool_name: str,
        arguments: Dict[str, Any],
        request_id: Union[str, int]
    ) -> MCPMessage:
        """
        Create a tools/call request message.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            request_id: Request ID
        
        Returns:
            MCPMessage object
        """
        return MCPMessage(
            jsonrpc="2.0",
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            },
            id=request_id,
            message_type=MCPMessageType.TOOLS_CALL,
            tool_name=tool_name,
            tool_arguments=arguments
        )
    
    @staticmethod
    def create_response(
        request_id: Union[str, int],
        result: Any
    ) -> MCPMessage:
        """
        Create a success response message.
        
        Args:
            request_id: ID of the request being responded to
            result: Result data
        
        Returns:
            MCPMessage object
        """
        return MCPMessage(
            jsonrpc="2.0",
            id=request_id,
            result=result,
            message_type=MCPMessageType.RESPONSE
        )
    
    @staticmethod
    def create_error(
        request_id: Union[str, int],
        code: int,
        message: str,
        data: Optional[Any] = None
    ) -> MCPMessage:
        """
        Create an error response message.
        
        Args:
            request_id: ID of the request being responded to
            code: Error code
            message: Error message
            data: Optional error data
        
        Returns:
            MCPMessage object
        """
        error = {
            "code": code,
            "message": message
        }
        
        if data is not None:
            error["data"] = data
        
        return MCPMessage(
            jsonrpc="2.0",
            id=request_id,
            error=error,
            message_type=MCPMessageType.ERROR
        )
    
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> tuple:
        """
        Validate MCP message format.
        
        Returns:
            (is_valid: bool, error_message: str)
        """
        # Check JSON-RPC version
        if not isinstance(message, dict):
            return False, "Message must be a JSON object"
        
        if "jsonrpc" not in message:
            return False, "Missing 'jsonrpc' field"
        
        if message["jsonrpc"] != "2.0":
            return False, "Invalid JSON-RPC version (must be '2.0')"
        
        # Check message structure
        has_method = "method" in message
        has_result = "result" in message
        has_error = "error" in message
        
        if not has_method and not has_result and not has_error:
            return False, "Message must have 'method' (request) or 'result'/'error' (response)"
        
        if has_method and (has_result or has_error):
            return False, "Message cannot have both 'method' and 'result'/'error'"
        
        if has_result and has_error:
            return False, "Message cannot have both 'result' and 'error'"
        
        # Validate request
        if has_method:
            if not isinstance(message["method"], str):
                return False, "'method' must be a string"
            
            if "params" in message and not isinstance(message["params"], (dict, list)):
                return False, "'params' must be an object or array"
        
        # Validate response
        if has_result or has_error:
            if "id" not in message:
                return False, "Response must have 'id'"
        
        return True, ""


class MCPErrorCode:
    """Standard JSON-RPC 2.0 and MCP-specific error codes"""
    # JSON-RPC 2.0 standard errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific errors (use -32000 to -32099 range)
    TOOL_NOT_FOUND = -32000
    TOOL_EXECUTION_ERROR = -32001
    RESOURCE_NOT_FOUND = -32002
    RESOURCE_ACCESS_DENIED = -32003
    SECURITY_VIOLATION = -32004  # For blocked requests
    RATE_LIMIT_EXCEEDED = -32005

