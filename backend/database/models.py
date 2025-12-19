"""
Database Models for SAFE-MCP-Platform
Production-grade SQLAlchemy models
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    """User/Tenant model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_super_admin = Column(Boolean, default=False)
    
    # Token for session management
    current_token = Column(String(255), nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    last_login_at = Column(DateTime(timezone=True), nullable=True)


class Detection(Base):
    """Detection log entry."""
    
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Request Info
    request_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Detection Info
    technique_id = Column(String(20), nullable=False, index=True)
    technique_name = Column(String(255), nullable=False)
    input_text = Column(Text, nullable=False)
    
    # MCP-Specific Fields
    mcp_method = Column(String(50), nullable=True, index=True)  # tools/call, resources/read, etc.
    mcp_tool_name = Column(String(255), nullable=True, index=True)  # read_file, git_commit, etc.
    mcp_tool_arguments = Column(JSON, nullable=True)  # Tool arguments
    mcp_server_name = Column(String(100), nullable=True)  # filesystem, git, gmail, etc.
    
    # Results
    blocked = Column(Boolean, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Detection Methods
    pattern_triggered = Column(Boolean, default=False)
    pattern_confidence = Column(Float, default=0.0)
    
    ml_triggered = Column(Boolean, default=False)
    ml_confidence = Column(Float, default=0.0)
    
    rules_triggered = Column(Boolean, default=False)
    rules_confidence = Column(Float, default=0.0)
    
    behavioral_triggered = Column(Boolean, default=False)
    behavioral_confidence = Column(Float, default=0.0)
    
    # Evidence
    evidence = Column(JSON, nullable=True)  # Array of evidence strings
    patterns_matched = Column(JSON, nullable=True)  # Array of matched patterns
    rules_violated = Column(JSON, nullable=True)  # Array of violated rules
    
    # Performance
    latency_ms = Column(Float, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_technique_blocked', 'technique_id', 'blocked'),
        Index('idx_user_detected_at', 'user_id', 'detected_at'),
        Index('idx_risk_detected_at', 'risk_level', 'detected_at'),
    )


class TechniqueConfig(Base):
    """Technique configuration storage."""
    
    __tablename__ = "technique_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Technique Info
    technique_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    tactic = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Detection Config (JSON)
    detection_config = Column(JSON, nullable=False)
    
    # Examples
    malicious_examples = Column(JSON, nullable=True)
    benign_examples = Column(JSON, nullable=True)
    
    # Response Action
    response_action = Column(String(20), default="BLOCK")  # BLOCK, WARN, LOG
    
    # Status
    enabled = Column(Boolean, default=True, index=True)
    
    # Metadata
    contributor = Column(String(255), nullable=True)
    version = Column(String(20), default="1.0")
    
    # Stats
    total_detections = Column(Integer, default=0)
    true_positives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserSession(Base):
    """User session tracking for behavioral analysis."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    
    # Session Stats
    total_requests = Column(Integer, default=0)
    blocked_requests = Column(Integer, default=0)
    risk_score = Column(Float, default=0.0)
    
    # Behavioral Patterns
    techniques_attempted = Column(JSON, default=[])  # List of technique IDs
    attack_patterns = Column(JSON, default=[])  # Detected attack patterns
    
    # Timestamps
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Status
    is_suspicious = Column(Boolean, default=False, index=True)
    is_blocked = Column(Boolean, default=False, index=True)


class SystemMetrics(Base):
    """System performance metrics."""
    
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Metric Info
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # ms, count, percent, etc.
    
    # Context
    service_name = Column(String(50), nullable=True)  # admin, detection, gateway
    technique_id = Column(String(20), nullable=True)
    
    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_metric_recorded', 'metric_name', 'recorded_at'),
    )
