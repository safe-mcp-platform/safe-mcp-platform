"""
Detection Service
High-performance detection API
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import structlog
import uvicorn

from config import settings
from database import init_db, close_db
from engine.detector import get_detection_engine

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="SAFE-MCP Detection Service",
    version=settings.APP_VERSION,
    description="High-performance MCP threat detection API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class DetectionRequest(BaseModel):
    """Detection request."""
    technique_id: str = Field(..., description="Technique ID (e.g., SAFE-T1102)")
    input_text: str = Field(..., description="Text to analyze", max_length=10000)
    user_id: Optional[str] = Field(None, description="User ID for tracking")
    session_id: Optional[str] = Field(None, description="Session ID for behavioral analysis")
    request_id: Optional[str] = Field(None, description="Request ID for correlation")


class DetectionResponse(BaseModel):
    """Detection response."""
    blocked: bool
    confidence: float
    risk_level: str
    technique_id: str
    technique_name: str
    evidence: list
    methods_triggered: list
    latency_ms: float


# Startup/Shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Detection Service", port=settings.DETECTION_PORT)
    init_db()
    # Pre-load detection engine
    get_detection_engine()
    logger.info("Detection Service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Detection Service")
    close_db()


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "detection",
        "version": settings.APP_VERSION
    }


# Main detection endpoint
@app.post("/detect", response_model=DetectionResponse)
async def detect(request: DetectionRequest):
    """
    Run detection on input.
    
    Args:
        request: DetectionRequest with technique and input
    
    Returns:
        DetectionResponse with results
    """
    try:
        engine = get_detection_engine()
        
        context = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "request_id": request.request_id
        }
        
        result = await engine.detect(
            technique_id=request.technique_id,
            input_text=request.input_text,
            context=context
        )
        
        return DetectionResponse(
            blocked=result.blocked,
            confidence=result.confidence,
            risk_level=result.risk_level.value,
            technique_id=result.technique_id,
            technique_name=result.technique_name,
            evidence=result.evidence,
            methods_triggered=[m.value for m in result.methods_triggered],
            latency_ms=result.latency_ms or 0.0
        )
        
    except Exception as e:
        logger.error("Detection failed", error=str(e), technique=request.technique_id)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


# Batch detection endpoint
@app.post("/detect/batch")
async def detect_batch(requests: list[DetectionRequest]):
    """
    Run detection on multiple inputs.
    
    Args:
        requests: List of DetectionRequest
    
    Returns:
        List of DetectionResponse
    """
    results = []
    for req in requests:
        try:
            engine = get_detection_engine()
            context = {
                "user_id": req.user_id,
                "session_id": req.session_id,
                "request_id": req.request_id
            }
            
            result = await engine.detect(
                technique_id=req.technique_id,
                input_text=req.input_text,
                context=context
            )
            
            results.append(DetectionResponse(
                blocked=result.blocked,
                confidence=result.confidence,
                risk_level=result.risk_level.value,
                technique_id=result.technique_id,
                technique_name=result.technique_name,
                evidence=result.evidence,
                methods_triggered=[m.value for m in result.methods_triggered],
                latency_ms=result.latency_ms or 0.0
            ))
        except Exception as e:
            logger.error("Batch detection item failed", error=str(e))
            results.append(None)
    
    return results


# Techniques list endpoint
@app.get("/techniques")
async def list_techniques():
    """List all loaded techniques."""
    from engine.config_loader import get_config_loader
    loader = get_config_loader()
    techniques = loader.get_all_techniques()
    
    return {
        "total": len(techniques),
        "techniques": [
            {
                "id": t_id,
                "name": config.name,
                "severity": config.severity,
                "tactic": config.tactic
            }
            for t_id, config in techniques.items()
        ]
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Get service metrics."""
    # TODO: Implement Prometheus metrics
    return {
        "service": "detection",
        "status": "operational"
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.DETECTION_PORT,
        workers=settings.DETECTION_WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )

