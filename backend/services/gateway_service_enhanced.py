"""
Enhanced Gateway Service
MCP multiplexer with security detection
"""

from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import JSONResponse
import structlog
import uvicorn
import asyncio
from typing import Optional, Dict, Any
import os

from config import settings
from engine.detector import get_detection_engine
from gateway.mcp_protocol import MCPProtocol, MCPMessage, MCPErrorCode
from gateway.tool_router import ToolRouter
from gateway.upstream_manager import UpstreamServerManager
from utils.detection_logger import log_detection

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="SAFE-MCP Gateway",
    version=settings.APP_VERSION,
    description="MCP multiplexer with security detection"
)

# Global instances
mcp_protocol = MCPProtocol()
tool_router = ToolRouter()
upstream_manager: Optional[UpstreamServerManager] = None


@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup"""
    global upstream_manager
    
    logger.info("Starting SAFE-MCP Gateway", port=settings.GATEWAY_PORT)
    
    # Load upstream server config
    upstream_config = os.getenv(
        "UPSTREAM_CONFIG",
        os.path.expanduser("~/.safe-mcp/servers.json")
    )
    
    upstream_manager = UpstreamServerManager(upstream_config)
    
    try:
        upstream_manager.load_config()
        await upstream_manager.start_all()
        
        # Discover tools from all servers
        all_tools = await upstream_manager.discover_all_tools()
        
        # Register tools with router
        for server_id, tools in all_tools.items():
            server = upstream_manager.get_server(server_id)
            if server:
                tool_router.register_tools(
                    server_id,
                    server.config.name,
                    tools
                )
        
        logger.info(
            "Gateway initialized",
            servers=len(upstream_manager.servers),
            tools=len(tool_router.tool_map)
        )
        
    except Exception as e:
        logger.error("Failed to initialize gateway", error=str(e))
        # Continue anyway - can still handle detection API
    
    # Pre-load detection engine
    get_detection_engine()
    logger.info("SAFE-MCP Gateway ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if upstream_manager:
        await upstream_manager.stop_all()
    logger.info("Gateway shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    stats = tool_router.get_stats()
    return {
        "status": "healthy",
        "service": "gateway",
        "version": settings.APP_VERSION,
        "servers": stats["total_servers"],
        "tools": stats["total_tools"]
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint
    Handles JSON-RPC 2.0 MCP protocol
    """
    try:
        # Parse request
        raw_body = await request.body()
        raw_message = raw_body.decode("utf-8")
        
        message = mcp_protocol.parse_message(raw_message)
        
        logger.info(
            "MCP request received",
            method=message.method,
            id=message.id
        )
        
        # Validate request
        error_response = mcp_protocol.validate_request(message)
        if error_response:
            return JSONResponse(content=error_response.to_dict())
        
        # Handle different methods
        if message.method == MCPProtocol.INITIALIZE:
            result = mcp_protocol.handle_initialize(message.params or {})
            response = mcp_protocol.create_response(message.id, result)
            return JSONResponse(content=response.to_dict())
        
        elif message.method == MCPProtocol.TOOLS_LIST:
            # Return aggregated tool list
            tools = tool_router.get_all_tools()
            result = {"tools": tools}
            response = mcp_protocol.create_response(message.id, result)
            return JSONResponse(content=response.to_dict())
        
        elif message.method == MCPProtocol.TOOLS_CALL:
            # Handle tool call with security detection
            return await handle_tool_call(message)
        
        else:
            # Method not found
            response = mcp_protocol.create_error_response(
                message.id,
                MCPErrorCode.METHOD_NOT_FOUND,
                f"Method not found: {message.method}"
            )
            return JSONResponse(content=response.to_dict())
    
    except ValueError as e:
        # Parse error
        response = mcp_protocol.create_error_response(
            "null",
            MCPErrorCode.PARSE_ERROR,
            str(e)
        )
        return JSONResponse(content=response.to_dict())
    
    except Exception as e:
        logger.error("Error handling MCP request", error=str(e))
        response = mcp_protocol.create_error_response(
            message.id if 'message' in locals() else "null",
            MCPErrorCode.INTERNAL_ERROR,
            "Internal server error"
        )
        return JSONResponse(content=response.to_dict())


async def handle_tool_call(message: MCPMessage) -> JSONResponse:
    """
    Handle tool call with security detection
    """
    params = message.params or {}
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if not tool_name:
        response = mcp_protocol.create_error_response(
            message.id,
            MCPErrorCode.INVALID_PARAMS,
            "Tool name required"
        )
        return JSONResponse(content=response.to_dict())
    
    # Check if tool exists
    if not tool_router.has_tool(tool_name):
        response = mcp_protocol.create_error_response(
            message.id,
            MCPErrorCode.METHOD_NOT_FOUND,
            f"Tool not found: {tool_name}"
        )
        return JSONResponse(content=response.to_dict())
    
    # Get tool info
    tool_info = tool_router.get_tool_info(tool_name)
    server_id = tool_info.server_id
    
    # RUN SECURITY DETECTION
    detection_result = await run_detection(
        tool_name,
        arguments,
        params,
        server_id=server_id,
        server_name=tool_info.server_name
    )
    
    if detection_result["blocked"]:
        logger.warning(
            "Tool call blocked by security",
            tool=tool_name,
            technique=detection_result["technique"],
            confidence=detection_result["confidence"],
            server=tool_info.server_name
        )
        
        # Log to database
        if "detection_result_obj" in detection_result:
            await log_detection(
                detection_result["detection_result_obj"],
                mcp_method="tools/call",
                mcp_tool_name=tool_name,
                mcp_tool_arguments=arguments,
                mcp_server_name=tool_info.server_name
            )
        
        response = mcp_protocol.create_error_response(
            message.id,
            MCPErrorCode.SECURITY_VIOLATION,
            "Security policy violation",
            {
                "technique": detection_result["technique"],
                "confidence": detection_result["confidence"],
                "reason": detection_result["reason"],
                "evidence": detection_result["evidence"]
            }
        )
        return JSONResponse(content=response.to_dict())
    
    # Forward to upstream server
    server = upstream_manager.get_server(server_id)
    if not server:
        response = mcp_protocol.create_error_response(
            message.id,
            MCPErrorCode.INTERNAL_ERROR,
            "Upstream server not available"
        )
        return JSONResponse(content=response.to_dict())
    
    try:
        # Call tool on upstream server
        # Remove server prefix if present
        original_tool_name = tool_name.split("/")[-1]
        upstream_response = await server.call_tool(original_tool_name, arguments)
        
        # Check response for injection
        if "result" in upstream_response:
            sanitized_result = await sanitize_output(
                upstream_response["result"],
                tool_name
            )
            upstream_response["result"] = sanitized_result
        
        return JSONResponse(content=upstream_response)
        
    except Exception as e:
        logger.error(
            "Error calling upstream server",
            tool=tool_name,
            server=server.config.name,
            error=str(e)
        )
        response = mcp_protocol.create_error_response(
            message.id,
            MCPErrorCode.INTERNAL_ERROR,
            f"Error calling tool: {str(e)}"
        )
        return JSONResponse(content=response.to_dict())


async def run_detection(
    tool_name: str,
    arguments: Dict[str, Any],
    params: Dict[str, Any],
    server_id: str = None,
    server_name: str = None
) -> Dict[str, Any]:
    """
    Run security detection on tool call
    """
    engine = get_detection_engine()
    
    # Combine all input for detection
    input_text = str(arguments)
    context = {
        "tool": tool_name,
        "arguments": arguments,
        "params": params,
        "mcp_method": "tools/call",
        "mcp_tool_name": tool_name,
        "mcp_tool_arguments": arguments,
        "mcp_server_name": server_name
    }
    
    # Check for prompt injection (T1102)
    t1102_result = await engine.detect(
        technique_id="SAFE-T1102",
        input_text=input_text,
        context=context
    )
    
    if t1102_result.blocked:
        return {
            "blocked": True,
            "technique": "SAFE-T1102",
            "confidence": t1102_result.confidence,
            "reason": "Prompt injection detected",
            "evidence": t1102_result.evidence,
            "detection_result_obj": t1102_result
        }
    
    # Check for path traversal if tool involves file access
    if any(key in arguments for key in ["path", "file", "filename", "directory"]):
        path_value = arguments.get("path") or arguments.get("file") or \
                     arguments.get("filename") or arguments.get("directory")
        
        t1105_result = await engine.detect(
            technique_id="SAFE-T1105",
            input_text=str(path_value),
            context=context
        )
        
        if t1105_result.blocked:
            return {
                "blocked": True,
                "technique": "SAFE-T1105",
                "confidence": t1105_result.confidence,
                "reason": "Path traversal detected",
                "evidence": t1105_result.evidence,
                "detection_result_obj": t1105_result
            }
    
    # All checks passed
    return {
        "blocked": False,
        "confidence": 0.0,
        "technique": None,
        "reason": None,
        "evidence": []
    }


async def sanitize_output(result: Any, tool_name: str) -> Any:
    """
    Sanitize tool output for prompt injection
    """
    if not isinstance(result, (str, dict, list)):
        return result
    
    result_str = str(result)
    
    # Quick check for injection patterns
    engine = get_detection_engine()
    detection = await engine.detect(
        technique_id="SAFE-T1102",
        input_text=result_str,
        context={"tool": tool_name, "direction": "output"}
    )
    
    if detection.blocked:
        logger.warning(
            "Tool output sanitized",
            tool=tool_name,
            confidence=detection.confidence
        )
        return f"[CONTENT SANITIZED: Potential security threat detected in tool output]"
    
    return result


def main():
    """Run gateway service"""
    uvicorn.run(
        "services.gateway_service_enhanced:app",
        host="0.0.0.0",
        port=settings.GATEWAY_PORT,
        workers=settings.GATEWAY_WORKERS,
        log_level="info"
    )


if __name__ == "__main__":
    main()

