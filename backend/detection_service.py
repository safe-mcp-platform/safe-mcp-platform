"""
Detection Service - High-Concurrency Detection API

This service provides:
- Real-time MCP message detection
- Batch detection
- Technique catalog
- Performance-optimized (32 workers)

Port: 5001
Workers: 32
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

import uvicorn

from config import settings
from services.dynamic_detection_engine import detection_engine
from services.mcp_protocol_parser import MCPProtocolParser

# Initialize FastAPI
app = FastAPI(
    title="SAFE-MCP Detection Service",
    description="High-concurrency detection API",
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


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class DetectionRequest(BaseModel):
    """Single detection request"""
    message: Dict[str, Any]  # MCP message
    session_context: Optional[Dict[str, Any]] = None


class BatchDetectionRequest(BaseModel):
    """Batch detection request"""
    messages: List[Dict[str, Any]]


# =============================================================================
# STARTUP
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("=" * 60)
    print(f"🔍 SAFE-MCP Detection Service v{settings.app_version}")
    print("=" * 60)
    print(f"📊 Techniques loaded: {len(detection_engine.techniques)}")
    print(f"🛡️  Mitigations loaded: {len(detection_engine.mitigations)}")
    print(f"📡 Port: {settings.detection_port}")
    print(f"⚡ Workers: {settings.detection_uvicorn_workers}")
    print(f"🚀 Max concurrent: {settings.detection_max_concurrent_requests}")
    print("=" * 60)


# =============================================================================
# HEALTH & INFO
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "detection",
        "version": settings.app_version,
        "techniques_loaded": len(detection_engine.techniques),
        "mitigations_loaded": len(detection_engine.mitigations),
        "ml_detection_enabled": settings.enable_ml_detection,
        "detection_methods": {
            "pattern": settings.enable_pattern_detection,
            "behavioral": settings.enable_behavioral_detection,
            "ml_model": settings.enable_ml_detection,
            "rule": settings.enable_rule_detection
        }
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SAFE-MCP Detection Service",
        "version": settings.app_version,
        "description": "High-concurrency MCP threat detection",
        "endpoints": {
            "/health": "Health check",
            "/v1/detect": "Detect threats in MCP message",
            "/v1/detect/batch": "Batch detection",
            "/v1/techniques": "List loaded techniques"
        },
        "stats": {
            "techniques": len(detection_engine.techniques),
            "mitigations": len(detection_engine.mitigations)
        }
    }


# =============================================================================
# DETECTION ENDPOINTS
# =============================================================================

@app.post("/v1/detect")
async def detect_message(request: DetectionRequest):
    """
    Detect threats in a single MCP message.
    
    This endpoint runs ALL enabled SAFE-T techniques in parallel
    and returns aggregated results.
    
    Example request:
    {
        "message": {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {"path": "/etc/passwd"}
            },
            "id": 1
        }
    }
    """
    try:
        start_time = datetime.utcnow()
        
        # Parse MCP message
        parser = MCPProtocolParser()
        mcp_message = parser.parse(request.message)
        
        # Run detection
        result = await detection_engine.detect_all(
            mcp_message=mcp_message,
            session_context=request.session_context
        )
        
        # Calculate latency
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Return results
        response = result.to_dict()
        response["latency_ms"] = round(latency_ms, 2)
        response["timestamp"] = datetime.utcnow().isoformat()
        
        return response
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid MCP message: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")


@app.post("/v1/detect/batch")
async def detect_batch(request: BatchDetectionRequest):
    """
    Batch detection - process multiple messages.
    
    Example request:
    {
        "messages": [
            {"jsonrpc": "2.0", "method": "tools/call", ...},
            {"jsonrpc": "2.0", "method": "resources/read", ...}
        ]
    }
    """
    import asyncio
    
    parser = MCPProtocolParser()
    
    # Parse all messages
    try:
        mcp_messages = [parser.parse(msg) for msg in request.messages]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid MCP message: {str(e)}")
    
    # Run detections in parallel
    tasks = [
        detection_engine.detect_all(mcp_message=msg, session_context=None)
        for msg in mcp_messages
    ]
    
    try:
        results = await asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch detection error: {str(e)}")
    
    return {
        "total": len(results),
        "results": [r.to_dict() for r in results]
    }


# =============================================================================
# TECHNIQUE CATALOG
# =============================================================================

@app.get("/v1/techniques")
async def list_techniques(tactic: Optional[str] = None, enabled: Optional[bool] = None):
    """
    List loaded SAFE-T techniques.
    
    Query params:
    - tactic: Filter by tactic (e.g., "Initial Access")
    - enabled: Filter by enabled status
    """
    techniques = []
    
    for tech_id, tech_config in detection_engine.techniques.items():
        # Apply filters
        if tactic and tech_config.get("tactic", "").lower() != tactic.lower():
            continue
        
        if enabled is not None and tech_config.get("enabled", True) != enabled:
            continue
        
        techniques.append({
            "id": tech_id,
            "name": tech_config.get("name", "Unknown"),
            "tactic": tech_config.get("tactic", "Unknown"),
            "severity": tech_config.get("severity", "MEDIUM"),
            "enabled": tech_config.get("enabled", True),
            "detection_method": tech_config.get("detection", {}).get("method", "unknown")
        })
    
    techniques.sort(key=lambda t: t["id"])
    
    return {
        "total": len(techniques),
        "techniques": techniques
    }


@app.get("/v1/techniques/{technique_id}")
async def get_technique_details(technique_id: str):
    """Get full details of a specific technique"""
    tech_config = detection_engine.techniques.get(technique_id)
    
    if not tech_config:
        raise HTTPException(status_code=404, detail="Technique not found")
    
    return tech_config


# =============================================================================
# MITIGATIONS
# =============================================================================

@app.get("/v1/mitigations")
async def list_mitigations():
    """List all loaded SAFE-M mitigations"""
    mitigations = []
    
    for mit_id, mit_config in detection_engine.mitigations.items():
        mitigations.append({
            "id": mit_id,
            "name": mit_config.get("name", "Unknown"),
            "effectiveness": mit_config.get("effectiveness", "MEDIUM"),
            "enabled": mit_config.get("enabled", True),
            "techniques_count": len(mit_config.get("techniques_mitigated", []))
        })
    
    mitigations.sort(key=lambda m: m["id"])
    
    return {
        "total": len(mitigations),
        "mitigations": mitigations
    }


@app.get("/v1/mitigations/{mitigation_id}")
async def get_mitigation_details(mitigation_id: str):
    """Get full details of a specific mitigation"""
    mit_config = detection_engine.mitigations.get(mitigation_id)
    
    if not mit_config:
        raise HTTPException(status_code=404, detail="Mitigation not found")
    
    return mit_config


# =============================================================================
# STATISTICS
# =============================================================================

@app.get("/v1/stats")
async def get_detection_stats():
    """Get detection engine statistics"""
    # Count techniques by tactic
    tactics = {}
    for tech_config in detection_engine.techniques.values():
        tactic = tech_config.get("tactic", "Unknown")
        tactics[tactic] = tactics.get(tactic, 0) + 1
    
    # Count techniques by severity
    severities = {}
    for tech_config in detection_engine.techniques.values():
        severity = tech_config.get("severity", "MEDIUM")
        severities[severity] = severities.get(severity, 0) + 1
    
    # Count techniques by detection method
    methods = {}
    for tech_config in detection_engine.techniques.values():
        method = tech_config.get("detection", {}).get("method", "unknown")
        methods[method] = methods.get(method, 0) + 1
    
    return {
        "techniques": {
            "total": len(detection_engine.techniques),
            "by_tactic": tactics,
            "by_severity": severities,
            "by_method": methods
        },
        "mitigations": {
            "total": len(detection_engine.mitigations)
        }
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "detection_service:app",
        host=settings.host,
        port=settings.detection_port,
        workers=settings.detection_uvicorn_workers,
        log_level=settings.log_level.lower()
    )

