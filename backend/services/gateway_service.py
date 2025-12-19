"""
Gateway Service
Transparent MCP protocol proxy with detection
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import structlog
import uvicorn
from typing import Optional

from config import settings
from engine.detector import get_detection_engine

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="SAFE-MCP Gateway",
    version=settings.APP_VERSION,
    description="Transparent MCP proxy with security detection"
)


# Startup
@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup."""
    logger.info("Starting MCP Gateway", port=settings.GATEWAY_PORT)
    # Pre-load detection engine
    get_detection_engine()
    logger.info("MCP Gateway ready")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "gateway",
        "version": settings.APP_VERSION
    }


# MCP proxy endpoint
@app.post("/mcp")
async def mcp_proxy(request: Request):
    """
    Proxy MCP requests with security checks.
    
    This endpoint:
    1. Receives MCP JSON-RPC 2.0 requests
    2. Runs detection on tool calls
    3. Forwards to actual MCP server if safe
    4. Returns response
    """
    try:
        # Parse MCP request
        mcp_request = await request.json()
        
        # Extract method and params
        method = mcp_request.get("method", "")
        params = mcp_request.get("params", {})
        
        # Check if this is a tool call
        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            # Run detection (basic prompt injection check)
            engine = get_detection_engine()
            
            # Check tool description for injection
            tool_desc = str(arguments)  # In production, extract actual tool description
            
            result = await engine.detect(
                technique_id="SAFE-T1102",
                input_text=tool_desc,
                context={"method": method, "tool": tool_name}
            )
            
            if result.blocked:
                logger.warning(
                    "MCP request blocked",
                    tool=tool_name,
                    confidence=result.confidence,
                    evidence=result.evidence
                )
                
                return JSONResponse(
                    status_code=403,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": "Request blocked by security gateway",
                            "data": {
                                "reason": "Potential security threat detected",
                                "confidence": result.confidence,
                                "risk_level": result.risk_level.value
                            }
                        },
                        "id": mcp_request.get("id")
                    }
                )
        
        # If safe, forward to actual MCP server
        # TODO: Configure actual MCP server URL
        mcp_server_url = request.headers.get("X-MCP-Server-URL", "http://localhost:8000/mcp")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                mcp_server_url,
                json=mcp_request,
                timeout=settings.REQUEST_TIMEOUT
            )
            
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
            
    except Exception as e:
        logger.error("Gateway proxy error", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal gateway error",
                    "data": {"error": str(e)}
                },
                "id": mcp_request.get("id") if 'mcp_request' in locals() else None
            }
        )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.GATEWAY_PORT,
        workers=settings.GATEWAY_WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )

