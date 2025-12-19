"""
Type definitions for detection system
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DetectionMethod(str, Enum):
    """Detection method types."""
    PATTERN = "pattern"
    ML_MODEL = "ml_model"
    RULES = "rules"
    BEHAVIORAL = "behavioral"


class PatternResult(BaseModel):
    """Pattern matching result."""
    triggered: bool = False
    confidence: float = 0.0
    patterns_matched: List[str] = []


class MLResult(BaseModel):
    """ML inference result."""
    triggered: bool = False
    confidence: float = 0.0
    model_name: str = ""
    prediction: Optional[str] = None


class RuleResult(BaseModel):
    """Rule validation result."""
    triggered: bool = False
    confidence: float = 0.0
    rules_violated: List[str] = []
    reasons: List[str] = []


class BehavioralResult(BaseModel):
    """Behavioral analysis result."""
    triggered: bool = False
    confidence: float = 0.0
    patterns_detected: List[str] = []
    risk_score: float = 0.0


class DetectionResult(BaseModel):
    """Final detection result."""
    
    # Technique Info
    technique_id: str
    technique_name: str
    
    # Decision
    blocked: bool
    confidence: float
    risk_level: RiskLevel
    
    # Method Results
    pattern_result: Optional[PatternResult] = None
    ml_result: Optional[MLResult] = None
    rule_result: Optional[RuleResult] = None
    behavioral_result: Optional[BehavioralResult] = None
    
    # Evidence
    evidence: List[str] = []
    methods_triggered: List[DetectionMethod] = []
    
    # Performance
    latency_ms: Optional[float] = None
    
    # Context
    input_text: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class TechniqueDetectionConfig(BaseModel):
    """Detection configuration for a technique."""
    
    patterns: Optional[Dict[str, Any]] = None
    ml_model: Optional[Dict[str, Any]] = None
    rules: Optional[Dict[str, Any]] = None
    behavioral: Optional[Dict[str, Any]] = None


class TechniqueConfig(BaseModel):
    """Complete technique configuration."""
    
    id: str
    name: str
    severity: str
    tactic: str
    description: str
    
    detection: TechniqueDetectionConfig
    
    examples: Optional[Dict[str, List[str]]] = None
    response: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

