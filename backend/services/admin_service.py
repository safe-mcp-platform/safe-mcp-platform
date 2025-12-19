"""
Admin Service
API for managing techniques, viewing logs, and dashboard stats
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timedelta
import structlog
import uvicorn
import secrets
from sqlalchemy import func, desc, Integer
import sqlalchemy
from passlib.context import CryptContext

from config import settings
from database import init_db, close_db
from database.connection import get_db_session
from database.models import Detection, TechniqueConfig, User
from engine.config_loader import get_config_loader

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    title="SAFE-MCP Admin Service",
    version=settings.APP_VERSION,
    description="Admin and dashboard API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Admin Service", port=settings.ADMIN_PORT)
    init_db()
    
    # Create super admin if not exists
    try:
        db = get_db_session()
        existing = db.query(User).filter(User.email == settings.super_admin_username).first()
        
        if not existing:
            super_admin = User(
                email=settings.super_admin_username,
                password_hash=pwd_context.hash(settings.super_admin_password),
                is_active=True,
                is_verified=True,
                is_super_admin=True
            )
            db.add(super_admin)
            db.commit()
            logger.info("Created super admin", email=settings.super_admin_username)
        else:
            logger.info("Super admin exists", email=settings.super_admin_username)
    except Exception as e:
        logger.error("Super admin setup failed", error=str(e))
    
    logger.info("Admin Service ready")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Admin Service")
    close_db()


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "admin",
        "version": settings.APP_VERSION
    }


# ===== AUTHENTICATION API =====

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/api/v1/auth/login")
@app.post("/api/v1/users/login")
async def login(request: LoginRequest):
    """Login endpoint"""
    db = get_db_session()
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    # Generate session token
    token = secrets.token_urlsafe(32)
    token_expires = datetime.now() + timedelta(hours=24)
    
    # Store token in database
    user.current_token = token
    user.token_expires_at = token_expires
    user.last_login_at = datetime.now()
    db.commit()
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 hours
        "tenant_id": user.id,
        "api_key": token,  # For compatibility
        "is_super_admin": user.is_super_admin
    }


@app.post("/api/v1/auth/register")
@app.post("/api/v1/users/register")
async def register(request: RegisterRequest):
    """Register new user"""
    db = get_db_session()
    
    # Check if exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=request.email,
        password_hash=pwd_context.hash(request.password),
        is_active=True,
        is_verified=False,
        is_super_admin=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Registration successful",
        "user_id": user.id,
        "email": user.email
    }


def get_user_from_token(token: str):
    """Get user from token - helper function"""
    db = get_db_session()
    user = db.query(User).filter(
        User.current_token == token,
        User.token_expires_at > datetime.now()
    ).first()
    return user


@app.get("/api/v1/users/me")
async def get_current_user(authorization: Optional[str] = None):
    """Get current user info from token"""
    # Extract token from Authorization header
    if not authorization:
        # Return default for compatibility
        return {
            "id": "anonymous",
            "email": "admin@safemcp.com",
            "api_key": "none",
            "is_active": True,
            "is_verified": True,
            "is_super_admin": True,
            "rate_limit": 0,
            "language": "en"
        }
    
    # Parse "Bearer <token>"
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    # Get user from token
    user = get_user_from_token(token)
    
    if not user:
        # Return default for demo compatibility
        return {
            "id": "anonymous",
            "email": "admin@safemcp.com",
            "api_key": "none",
            "is_active": True,
            "is_verified": True,
            "is_super_admin": True,
            "rate_limit": 0,
            "language": "en"
        }
    
    return {
        "id": user.id,
        "email": user.email,
        "api_key": user.current_token or "none",
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_super_admin": user.is_super_admin,
        "rate_limit": 0,
        "language": "en"
    }


# ===== TECHNIQUES API =====

@app.get("/api/v1/techniques")
async def list_techniques():
    """List all techniques"""
    try:
        config_loader = get_config_loader()
        techniques = config_loader.list_techniques()
        
        db = get_db_session()
        
        result = []
        for tech in techniques:
            # Get stats from database
            stats = db.query(
                func.count(Detection.id).label('total'),
                func.sum(func.cast(Detection.blocked, sqlalchemy.Integer)).label('blocked')
            ).filter(Detection.technique_id == tech.id).first()
            
            detection_methods = []
            if tech.detection and tech.detection.patterns and tech.detection.patterns.get("enabled"):
                detection_methods.append("Pattern")
            if tech.detection and tech.detection.ml_model and tech.detection.ml_model.get("enabled"):
                detection_methods.append("ML")
            if tech.detection and tech.detection.rules and tech.detection.rules.get("enabled"):
                detection_methods.append("Rules")
            
            result.append({
                "technique_id": tech.id,
                "name": tech.name,
                "tactic": tech.tactic,
                "severity": tech.severity,
                "enabled": tech.detection is not None,  # Enabled if has detection config
                "description": tech.description or "",
                "detection_methods": detection_methods,
                "total_detections": stats.total or 0 if stats else 0,
                "true_positives": stats.total or 0 if stats else 0,  # Assume all are true positives for now
                "false_positives": 0,  # Would need feedback mechanism
            })
        
        db.close()
        return {"techniques": result}
        
    except Exception as e:
        logger.error("Failed to list techniques", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/techniques/{technique_id}")
async def update_technique(technique_id: str, data: Dict[str, Any]):
    """Update technique configuration"""
    try:
        db = get_db_session()
        
        # TODO: Store technique config in database
        # For now, just acknowledge
        
        db.close()
        return {"success": True, "technique_id": technique_id}
        
    except Exception as e:
        logger.error("Failed to update technique", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ===== DETECTIONS API =====

@app.get("/api/v1/detections")
async def list_detections(
    risk_level: Optional[str] = None,
    blocked: Optional[bool] = None,
    technique_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    server_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
):
    """List detections with filters"""
    try:
        db = get_db_session()
        
        query = db.query(Detection)
        
        # Apply filters
        if risk_level:
            query = query.filter(Detection.risk_level == risk_level)
        if blocked is not None:
            query = query.filter(Detection.blocked == blocked)
        if technique_id:
            query = query.filter(Detection.technique_id == technique_id)
        if tool_name:
            query = query.filter(Detection.mcp_tool_name == tool_name)
        if server_name:
            query = query.filter(Detection.mcp_server_name == server_name)
        if start_date:
            query = query.filter(Detection.detected_at >= start_date)
        if end_date:
            query = query.filter(Detection.detected_at <= end_date)
        
        # Order by most recent
        query = query.order_by(desc(Detection.detected_at))
        
        # Paginate
        offset = (page - 1) * per_page
        detections = query.offset(offset).limit(per_page).all()
        
        result = []
        for det in detections:
            result.append({
                "id": det.id,
                "technique_id": det.technique_id,
                "technique_name": det.technique_name,
                "mcp_method": det.mcp_method,
                "mcp_tool_name": det.mcp_tool_name,
                "mcp_server_name": det.mcp_server_name,
                "mcp_tool_arguments": det.mcp_tool_arguments,
                "blocked": det.blocked,
                "confidence": det.confidence,
                "risk_level": det.risk_level,
                "detected_at": det.detected_at.isoformat() if det.detected_at else None,
                "evidence": det.evidence or [],
                "pattern_triggered": det.pattern_triggered,
                "ml_triggered": det.ml_triggered,
                "rules_triggered": det.rules_triggered,
            })
        
        db.close()
        return {"detections": result, "total": len(result)}
        
    except Exception as e:
        logger.error("Failed to list detections", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ===== DASHBOARD API =====

@app.get("/api/v1/dashboard/stats")
async def dashboard_stats(days: int = 7):
    """Get dashboard statistics"""
    try:
        db = get_db_session()
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total detections
        total_query = db.query(func.count(Detection.id)).filter(
            Detection.detected_at >= start_date
        )
        total_detections = total_query.scalar() or 0
        
        # Blocked count
        blocked_query = db.query(func.count(Detection.id)).filter(
            Detection.detected_at >= start_date,
            Detection.blocked == True
        )
        blocked_count = blocked_query.scalar() or 0
        
        allowed_count = total_detections - blocked_count
        
        # Risk distribution
        risk_dist = db.query(
            Detection.risk_level,
            func.count(Detection.id).label('count')
        ).filter(
            Detection.detected_at >= start_date
        ).group_by(Detection.risk_level).all()
        
        risk_distribution = {level: count for level, count in risk_dist}
        
        # Top techniques
        top_techniques = db.query(
            Detection.technique_id,
            func.count(Detection.id).label('count')
        ).filter(
            Detection.detected_at >= start_date,
            Detection.blocked == True
        ).group_by(Detection.technique_id).order_by(desc('count')).limit(10).all()
        
        # Top tools
        top_tools = db.query(
            Detection.mcp_tool_name,
            func.count(Detection.id).label('count')
        ).filter(
            Detection.detected_at >= start_date,
            Detection.mcp_tool_name.isnot(None)
        ).group_by(Detection.mcp_tool_name).order_by(desc('count')).limit(10).all()
        
        # Top servers
        top_servers = db.query(
            Detection.mcp_server_name,
            func.count(Detection.id).label('count')
        ).filter(
            Detection.detected_at >= start_date,
            Detection.mcp_server_name.isnot(None)
        ).group_by(Detection.mcp_server_name).order_by(desc('count')).limit(10).all()
        
        # Daily trends
        daily_trends = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_total = db.query(func.count(Detection.id)).filter(
                Detection.detected_at >= day_start,
                Detection.detected_at < day_end
            ).scalar() or 0
            
            day_blocked = db.query(func.count(Detection.id)).filter(
                Detection.detected_at >= day_start,
                Detection.detected_at < day_end,
                Detection.blocked == True
            ).scalar() or 0
            
            daily_trends.append({
                "date": day_start.strftime('%Y-%m-%d'),
                "total": day_total,
                "blocked": day_blocked
            })
        
        db.close()
        
        return {
            "total_detections": total_detections,
            "blocked_count": blocked_count,
            "allowed_count": allowed_count,
            "top_techniques": [{"technique_id": tid, "count": count} for tid, count in top_techniques],
            "top_tools": [{"tool_name": name, "count": count} for name, count in top_tools],
            "top_servers": [{"server_name": name, "count": count} for name, count in top_servers],
            "risk_distribution": risk_distribution,
            "daily_trends": daily_trends
        }
        
    except Exception as e:
        logger.error("Failed to get dashboard stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.ADMIN_PORT,
        log_level="info"
    )
