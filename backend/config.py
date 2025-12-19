"""
SAFE-MCP-Platform Configuration
Production-grade configuration management
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "SAFE-MCP-Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    
    # Super Admin (default credentials - CHANGE IN PRODUCTION!)
    super_admin_username: str = Field(
        default="admin@safemcp.com",
        env="SUPER_ADMIN_USERNAME"
    )
    super_admin_password: str = Field(
        default="admin123",
        env="SUPER_ADMIN_PASSWORD"
    )
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    ADMIN_PORT: int = Field(default=8000, env="ADMIN_PORT")
    DETECTION_PORT: int = Field(default=8001, env="DETECTION_PORT")
    GATEWAY_PORT: int = Field(default=8002, env="GATEWAY_PORT")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://safemcp:safemcp123@db:5432/safemcp_db",
        env="DATABASE_URL"
    )
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")
    
    # Detection Engine
    TECHNIQUES_DIR: str = Field(
        default="techniques",
        env="TECHNIQUES_DIR"
    )
    PATTERNS_DIR: str = Field(
        default="patterns",
        env="PATTERNS_DIR"
    )
    RULES_DIR: str = Field(
        default="rules",
        env="RULES_DIR"
    )
    
    # ML Models
    ML_MODELS_CACHE_DIR: str = Field(
        default="/tmp/huggingface_cache",
        env="ML_MODELS_CACHE_DIR"
    )
    ML_INFERENCE_TIMEOUT: int = Field(default=5, env="ML_INFERENCE_TIMEOUT")
    
    # Detection Thresholds
    # Pattern matching gets highest weight since it's most reliable for T1102/T1105
    PATTERN_CONFIDENCE_WEIGHT: float = 0.6
    RULE_CONFIDENCE_WEIGHT: float = 0.25
    ML_CONFIDENCE_WEIGHT: float = 0.10
    BEHAVIORAL_CONFIDENCE_WEIGHT: float = 0.05
    
    # Lowered threshold to allow pattern-only blocking
    # With pattern confidence ~0.95 * 0.6 weight = 0.57, attacks will block
    BLOCK_THRESHOLD: float = 0.5
    WARN_THRESHOLD: float = 0.3
    
    # Performance
    DETECTION_WORKERS: int = Field(default=32, env="DETECTION_WORKERS")
    GATEWAY_WORKERS: int = Field(default=24, env="GATEWAY_WORKERS")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "json"  # json or text
    
    # Security
    SECRET_KEY: str = Field(
        default="change-this-in-production-use-env-var",
        env="SECRET_KEY"
    )
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")  # For admin_service compatibility
    ALLOWED_ORIGINS: list = ["*"]  # Configure for production
    
    # Uvicorn Workers
    admin_uvicorn_workers: int = Field(default=1, env="ADMIN_UVICORN_WORKERS")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
