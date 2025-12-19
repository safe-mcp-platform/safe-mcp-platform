"""
Admin Service - Management & Dashboard API

This service provides:
- Authentication (login, register, verify)
- Application management
- API key management
- Technique configuration
- Analytics dashboards

Port: 5000
Workers: 2
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import uuid

import uvicorn

from config import settings
from database.connection import get_db, engine
from database.models import Base, Tenant, Application, ApiKey, SAFETechnique
from services.dynamic_detection_engine import detection_engine

# Initialize FastAPI
app = FastAPI(
    title="SAFE-MCP Admin Service",
    description="Management and dashboard API",
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

security = HTTPBearer(auto_error=False)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class CreateApplicationRequest(BaseModel):
    name: str
    description: Optional[str] = None


class CreateApiKeyRequest(BaseModel):
    application_id: str
    name: Optional[str] = None


# =============================================================================
# STARTUP
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("=" * 60)
    print(f"🚀 SAFE-MCP Admin Service v{settings.app_version}")
    print("=" * 60)
    
    # Create tables
    print("📊 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    # Create super admin if doesn't exist
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    try:
        db = next(get_db())
        existing = db.query(Tenant).filter(Tenant.email == settings.super_admin_username).first()
        
        if not existing:
            super_admin = Tenant(
                email=settings.super_admin_username,
                password_hash=pwd_context.hash(settings.super_admin_password),
                is_active=True,
                is_verified=True,
                is_super_admin=True
            )
            db.add(super_admin)
            db.commit()
            print(f"✅ Created super admin: {settings.super_admin_username}")
        else:
            print(f"✅ Super admin exists: {settings.super_admin_username}")
        
        db.close()
    except Exception as e:
        print(f"⚠️  Super admin setup warning: {e}")
    
    print(f"📡 Port: {settings.admin_port}")
    print(f"⚡ Workers: {settings.admin_uvicorn_workers}")
    print("=" * 60)


# =============================================================================
# HEALTH & INFO
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "admin",
        "version": settings.app_version,
        "techniques_loaded": len(detection_engine.techniques)
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SAFE-MCP Admin Service",
        "version": settings.app_version,
        "description": "Management and dashboard API",
        "endpoints": {
            "/health": "Health check",
            "/api/v1/auth/login": "Login",
            "/api/v1/auth/register": "Register",
            "/api/v1/applications": "Application management",
            "/api/v1/api-keys": "API key management",
            "/api/v1/techniques": "Technique catalog"
        }
    }


# =============================================================================
# AUTHENTICATION (Simplified)
# =============================================================================

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Simple login endpoint"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Find tenant
    tenant = db.query(Tenant).filter(Tenant.email == request.email).first()
    
    if not tenant or not pwd_context.verify(request.password, tenant.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate simple token (in production, use JWT)
    token = secrets.token_urlsafe(32)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_id": str(tenant.id),
        "email": tenant.email,
        "is_super_admin": tenant.is_super_admin
    }


@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Simple registration endpoint"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Check if exists
    existing = db.query(Tenant).filter(Tenant.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create tenant
    tenant = Tenant(
        email=request.email,
        password_hash=pwd_context.hash(request.password),
        is_active=True,
        is_verified=False,
        is_super_admin=False
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    return {
        "message": "Registration successful",
        "tenant_id": str(tenant.id),
        "email": tenant.email
    }


# =============================================================================
# APPLICATION MANAGEMENT
# =============================================================================

@app.get("/api/v1/applications")
async def list_applications(db: Session = Depends(get_db)):
    """List all applications (simplified - no auth check)"""
    apps = db.query(Application).all()
    
    return {
        "applications": [
            {
                "id": str(app.id),
                "name": app.name,
                "description": app.description,
                "is_active": app.is_active,
                "created_at": app.created_at.isoformat() if app.created_at else None
            }
            for app in apps
        ]
    }


@app.post("/api/v1/applications")
async def create_application(request: CreateApplicationRequest, db: Session = Depends(get_db)):
    """Create new application (simplified)"""
    # For demo, use first tenant
    tenant = db.query(Tenant).first()
    if not tenant:
        raise HTTPException(status_code=400, detail="No tenant found")
    
    app = Application(
        tenant_id=tenant.id,
        name=request.name,
        description=request.description,
        is_active=True
    )
    
    db.add(app)
    db.commit()
    db.refresh(app)
    
    return {
        "message": "Application created",
        "application": {
            "id": str(app.id),
            "name": app.name,
            "description": app.description
        }
    }


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

@app.post("/api/v1/api-keys")
async def create_api_key(request: CreateApiKeyRequest, db: Session = Depends(get_db)):
    """Create API key for application"""
    # Verify application exists
    app = db.query(Application).filter(Application.id == request.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Generate key
    key = f"sk-safemcp-{secrets.token_urlsafe(32)}"
    
    api_key = ApiKey(
        tenant_id=app.tenant_id,
        application_id=app.id,
        key=key,
        name=request.name or "Default Key",
        is_active=True
    )
    
    db.add(api_key)
    db.commit()
    
    return {
        "message": "API key created",
        "api_key": key,
        "warning": "Save this key - it won't be shown again!"
    }


@app.get("/api/v1/api-keys")
async def list_api_keys(application_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List API keys"""
    query = db.query(ApiKey)
    
    if application_id:
        query = query.filter(ApiKey.application_id == application_id)
    
    keys = query.all()
    
    return {
        "api_keys": [
            {
                "id": str(key.id),
                "name": key.name,
                "key": f"{key.key[:20]}...",  # Masked
                "is_active": key.is_active,
                "created_at": key.created_at.isoformat() if key.created_at else None
            }
            for key in keys
        ]
    }


# =============================================================================
# TECHNIQUE CATALOG
# =============================================================================

@app.get("/api/v1/techniques")
async def list_techniques():
    """List all SAFE-T techniques"""
    techniques = []
    
    for tech_id, tech_config in detection_engine.techniques.items():
        techniques.append({
            "id": tech_id,
            "name": tech_config.get("name", "Unknown"),
            "tactic": tech_config.get("tactic", "Unknown"),
            "severity": tech_config.get("severity", "MEDIUM"),
            "enabled": tech_config.get("enabled", True),
            "description": tech_config.get("description", "")[:200]  # Truncate
        })
    
    # Sort by ID
    techniques.sort(key=lambda t: t["id"])
    
    return {
        "total": len(techniques),
        "techniques": techniques
    }


@app.get("/api/v1/techniques/{technique_id}")
async def get_technique(technique_id: str):
    """Get technique details"""
    tech_config = detection_engine.techniques.get(technique_id)
    
    if not tech_config:
        raise HTTPException(status_code=404, detail="Technique not found")
    
    return tech_config


@app.get("/api/v1/techniques/by-tactic/{tactic}")
async def get_techniques_by_tactic(tactic: str):
    """Get techniques by tactic"""
    techniques = [
        {
            "id": tid,
            "name": config.get("name", "Unknown"),
            "severity": config.get("severity", "MEDIUM"),
            "enabled": config.get("enabled", True)
        }
        for tid, config in detection_engine.techniques.items()
        if config.get("tactic", "").lower() == tactic.lower()
    ]
    
    return {
        "tactic": tactic,
        "count": len(techniques),
        "techniques": techniques
    }


# =============================================================================
# STATISTICS
# =============================================================================

@app.get("/api/v1/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get platform statistics"""
    from database.models import MCPDetectionResult, MCPSession
    
    try:
        total_tenants = db.query(Tenant).count()
        total_apps = db.query(Application).count()
        total_keys = db.query(ApiKey).count()
        total_detections = db.query(MCPDetectionResult).count()
        total_sessions = db.query(MCPSession).count()
        
        return {
            "tenants": total_tenants,
            "applications": total_apps,
            "api_keys": total_keys,
            "detections": total_detections,
            "sessions": total_sessions,
            "techniques_loaded": len(detection_engine.techniques),
            "mitigations_loaded": len(detection_engine.mitigations)
        }
    except Exception as e:
        return {
            "error": str(e),
            "techniques_loaded": len(detection_engine.techniques),
            "mitigations_loaded": len(detection_engine.mitigations)
        }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "admin_service:app",
        host=settings.host,
        port=settings.admin_port,
        workers=settings.admin_uvicorn_workers,
        log_level=settings.log_level.lower()
    )

