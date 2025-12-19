"""
MCP Gateway Service - Transparent Security Proxy for MCP Protocol

This service acts as a transparent proxy between MCP clients and servers,
inspecting all traffic and blocking malicious requests in real-time.

Port: 5002
Workers: 24 (high concurrency)
Protocol: MCP (JSON-RPC 2.0)

Key Innovation: WAF-style protection for AI agents!
"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from services.mcp_protocol_parser import MCPProtocolParser, MCPMessage, MCPErrorCode
from services.dynamic_detection_engine import detection_engine
from database.connection import get_db_session
from database.models import MCPSession, MCPDetectionResult, MCPToolCall, Application

# Security bearer
security = HTTPBearer(auto_error=False)

# Create FastAPI app
app = FastAPI(
    title="SAFE-MCP Gateway",
    description="Transparent MCP security proxy with real-time threat detection",
    version=settings.app_version
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MCPGateway:
    """
    MCP Gateway - Transparent security proxy
    
    Flow:
    1. Client sends MCP request
    2. Parse and validate MCP protocol
    3. Run security detection (80+ SAFE-T techniques)
    4. If safe: forward to MCP server
    5. If unsafe: block and return error
    6. Intercept MCP server response
    7. Detect response safety
    8. Return to client
    """
    
    def __init__(self):
        self.parser = MCPProtocolParser()
        self.sessions: Dict[str, MCPSession] = {}  # In-memory session cache
    
    async def handle_request(
        self,
        raw_message: Dict[str, Any],
        application_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main request handler - intercepts and inspects MCP requests.
        
        Args:
            raw_message: Raw MCP message from client
            application_id: Application ID (from auth)
            user_id: Optional user ID
        
        Returns:
            MCP response (either forwarded or blocked)
        """
        request_id = str(uuid.uuid4())
        
        try:
            # 1. Parse MCP message
            mcp_message = self.parser.parse(raw_message)
            
            # 2. Get or create session
            session = await self._get_or_create_session(application_id, user_id)
            
            # 3. Run security detection
            detection_result = await detection_engine.detect_all(
                mcp_message=mcp_message,
                session_context=session
            )
            
            # 4. Log detection
            await self._log_detection(
                session=session,
                mcp_message=mcp_message,
                detection_result=detection_result,
                request_id=request_id
            )
            
            # 5. Make decision
            if detection_result.action == "BLOCK":
                # BLOCK: Return error to client
                return self._create_blocked_response(mcp_message, detection_result)
            
            # 6. ALLOW: Forward to MCP server (not implemented yet - would need MCP server config)
            # For now, return a success response
            return self._create_allowed_response(mcp_message, detection_result)
        
        except ValueError as e:
            # Invalid MCP message
            return self.parser.create_error(
                request_id=raw_message.get("id", "unknown"),
                code=MCPErrorCode.INVALID_REQUEST,
                message=str(e)
            ).to_dict()
        
        except Exception as e:
            print(f"❌ Gateway error: {e}")
            return self.parser.create_error(
                request_id=raw_message.get("id", "unknown"),
                code=MCPErrorCode.INTERNAL_ERROR,
                message="Internal gateway error"
            ).to_dict()
    
    async def _get_or_create_session(
        self,
        application_id: str,
        user_id: Optional[str]
    ) -> MCPSession:
        """Get existing session or create new one"""
        # Simple in-memory session management
        # In production, would use database or Redis
        
        session_key = f"{application_id}:{user_id or 'anonymous'}"
        
        if session_key not in self.sessions:
            # Create new session
            session = MCPSession(
                application_id=application_id,
                user_id=user_id,
                total_requests=0,
                blocked_requests=0,
                risk_score=0.0,
                is_active=True,
                metadata={}
            )
            self.sessions[session_key] = session
        
        session = self.sessions[session_key]
        session.total_requests += 1
        
        return session
    
    async def _log_detection(
        self,
        session: MCPSession,
        mcp_message: MCPMessage,
        detection_result: Any,
        request_id: str
    ):
        """Log detection result to database"""
        try:
            db = get_db_session()
            
            detection_record = MCPDetectionResult(
                session_id=session.id,
                application_id=session.application_id,
                timestamp=datetime.utcnow(),
                mcp_message_type=mcp_message.method,
                mcp_tool_name=mcp_message.tool_name,
                raw_message=mcp_message.raw,
                detected_techniques=[t.to_dict() for t in detection_result.matched_techniques],
                overall_risk_level=detection_result.overall_risk_level,
                action_taken=detection_result.action,
                confidence_score=detection_result.confidence,
                mitigations_applied=detection_result.mitigations,
                evidence={"detection_id": request_id}
            )
            
            db.add(detection_record)
            db.commit()
            db.close()
        
        except Exception as e:
            print(f"⚠️  Failed to log detection: {e}")
    
    def _create_blocked_response(
        self,
        mcp_message: MCPMessage,
        detection_result: Any
    ) -> Dict[str, Any]:
        """Create error response for blocked request"""
        # Format matched techniques
        techniques_str = ", ".join([
            f"{t.technique_id} ({t.technique_name})"
            for t in detection_result.matched_techniques
        ])
        
        error_msg = f"Request blocked - Security violation detected: {techniques_str}"
        
        return self.parser.create_error(
            request_id=mcp_message.id or "unknown",
            code=MCPErrorCode.SECURITY_VIOLATION,
            message=error_msg,
            data={
                "risk_level": detection_result.overall_risk_level,
                "matched_techniques": [t.technique_id for t in detection_result.matched_techniques],
                "confidence": detection_result.confidence,
                "mitigations": detection_result.mitigations
            }
        ).to_dict()
    
    def _create_allowed_response(
        self,
        mcp_message: MCPMessage,
        detection_result: Any
    ) -> Dict[str, Any]:
        """Create success response for allowed request"""
        # In production, this would forward to actual MCP server
        # For now, return a mock success response
        
        return self.parser.create_response(
            request_id=mcp_message.id or "unknown",
            result={
                "status": "allowed",
                "message": "Request passed security checks",
                "risk_level": detection_result.overall_risk_level,
                "note": "In production, this would be forwarded to the MCP server"
            }
        ).to_dict()


# Initialize gateway
gateway = MCPGateway()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-gateway",
        "version": settings.app_version,
        "techniques_loaded": len(detection_engine.techniques)
    }


@app.post("/v1/mcp")
async def mcp_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Main MCP endpoint - receives MCP protocol messages.
    
    This endpoint accepts JSON-RPC 2.0 messages and applies security.
    """
    # Get API key from header
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    api_key = credentials.credentials
    
    # Validate API key and get application
    # (Simplified - in production, would validate against database)
    application_id = "test-app-id"  # Mock
    user_id = None
    
    # Parse request body
    try:
        raw_message = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Handle request through gateway
    response = await gateway.handle_request(
        raw_message=raw_message,
        application_id=application_id,
        user_id=user_id
    )
    
    return JSONResponse(content=response)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SAFE-MCP Gateway",
        "version": settings.app_version,
        "description": "Transparent MCP security proxy",
        "endpoints": {
            "/v1/mcp": "Main MCP endpoint",
            "/health": "Health check"
        }
    }


def start_gateway_service():
    """Start the MCP Gateway service"""
    print("=" * 60)
    print(f"🛡️  SAFE-MCP Gateway Service v{settings.app_version}")
    print("=" * 60)
    print(f"Port: {settings.gateway_port}")
    print(f"Workers: {settings.gateway_uvicorn_workers}")
    print(f"Techniques loaded: {len(detection_engine.techniques)}")
    print(f"Ready to intercept MCP traffic!")
    print("=" * 60)
    
    uvicorn.run(
        "mcp_gateway_service:app",
        host=settings.host,
        port=settings.gateway_port,
        workers=settings.gateway_uvicorn_workers,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    start_gateway_service()

