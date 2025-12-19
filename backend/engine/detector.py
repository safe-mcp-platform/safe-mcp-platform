"""
Main Detection Engine
Aggregates all detection methods (Pattern, ML, Rules, Behavioral)
"""

import time
from typing import Optional, Dict, Any
import structlog

from utils.types import (
    DetectionResult, RiskLevel, DetectionMethod,
    PatternResult, MLResult, RuleResult, BehavioralResult
)
from config import settings
from .config_loader import get_config_loader
from .pattern_matcher import get_pattern_matcher
from .rule_engine import get_rule_engine
from .ml_inference import get_ml_engine

logger = structlog.get_logger()


class DetectionEngine:
    """Main detection engine - aggregates all detection methods."""
    
    def __init__(self):
        self.config_loader = get_config_loader()
        self.pattern_matcher = get_pattern_matcher()
        self.rule_engine = get_rule_engine()
        self.ml_engine = get_ml_engine()
        logger.info("Detection engine initialized")
    
    async def detect(
        self,
        technique_id: str,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DetectionResult:
        """
        Run detection for a technique.
        
        Args:
            technique_id: Technique ID (e.g., "SAFE-T1102")
            input_text: Text to analyze
            context: Additional context (user_id, session_id, etc.)
        
        Returns:
            DetectionResult with aggregated decision
        """
        start_time = time.time()
        context = context or {}
        
        # Load technique configuration
        technique_config = self.config_loader.get_technique(technique_id)
        if not technique_config:
            logger.warning(f"Technique not found: {technique_id}")
            return self._create_error_result(technique_id, input_text, "Technique not found")
        
        # Run all enabled detection methods
        pattern_result = None
        ml_result = None
        rule_result = None
        behavioral_result = None
        
        # 1. Pattern matching (fast, keep sync)
        if technique_config.detection.patterns and technique_config.detection.patterns.get("enabled"):
            patterns = self.config_loader.get_patterns(technique_id)
            case_sensitive = technique_config.detection.patterns.get("case_sensitive", False)
            pattern_result = self.pattern_matcher.match(input_text, patterns, case_sensitive)
        
        # 2. ML inference (async for non-blocking)
        if technique_config.detection.ml_model and technique_config.detection.ml_model.get("enabled"):
            model_name = technique_config.detection.ml_model.get("name")
            threshold = technique_config.detection.ml_model.get("threshold", 0.75)
            if model_name:
                ml_result = await self.ml_engine.predict_async(input_text, model_name, threshold)
        
        # 3. Rule validation (fast, keep sync)
        if technique_config.detection.rules and technique_config.detection.rules.get("enabled"):
            validator_path = technique_config.detection.rules.get("validator")
            if validator_path:
                rule_result = self.rule_engine.execute(validator_path, input_text, context)
        
        # 4. Behavioral analysis (placeholder - would need session state)
        # behavioral_result = self._run_behavioral_analysis(technique_id, input_text, context)
        
        # Aggregate results
        result = self._aggregate_results(
            technique_id,
            technique_config.name,
            input_text,
            pattern_result,
            ml_result,
            rule_result,
            behavioral_result,
            context
        )
        
        # Add latency
        latency_ms = (time.time() - start_time) * 1000
        result.latency_ms = latency_ms
        
        logger.info(
            "Detection completed",
            technique_id=technique_id,
            blocked=result.blocked,
            confidence=result.confidence,
            latency_ms=latency_ms
        )
        
        return result
    
    def _aggregate_results(
        self,
        technique_id: str,
        technique_name: str,
        input_text: str,
        pattern_result: Optional[PatternResult],
        ml_result: Optional[MLResult],
        rule_result: Optional[RuleResult],
        behavioral_result: Optional[BehavioralResult],
        context: Dict[str, Any]
    ) -> DetectionResult:
        """Aggregate results from all detection methods."""
        
        # Weighted ensemble voting
        total_confidence = 0.0
        active_methods = 0
        methods_triggered = []
        evidence = []
        
        # Pattern confidence
        if pattern_result and pattern_result.triggered:
            total_confidence += pattern_result.confidence * settings.PATTERN_CONFIDENCE_WEIGHT
            methods_triggered.append(DetectionMethod.PATTERN)
            evidence.append(f"Pattern match: {len(pattern_result.patterns_matched)} patterns")
            active_methods += settings.PATTERN_CONFIDENCE_WEIGHT
        
        # ML confidence
        if ml_result and ml_result.triggered:
            total_confidence += ml_result.confidence * settings.ML_CONFIDENCE_WEIGHT
            methods_triggered.append(DetectionMethod.ML_MODEL)
            evidence.append(f"ML model: {ml_result.confidence:.1%} malicious probability")
            active_methods += settings.ML_CONFIDENCE_WEIGHT
        
        # Rules confidence
        if rule_result and rule_result.triggered:
            total_confidence += rule_result.confidence * settings.RULE_CONFIDENCE_WEIGHT
            methods_triggered.append(DetectionMethod.RULES)
            evidence.extend([f"Rule violation: {r}" for r in rule_result.reasons[:3]])
            active_methods += settings.RULE_CONFIDENCE_WEIGHT
        
        # Behavioral confidence
        if behavioral_result and behavioral_result.triggered:
            total_confidence += behavioral_result.confidence * settings.BEHAVIORAL_CONFIDENCE_WEIGHT
            methods_triggered.append(DetectionMethod.BEHAVIORAL)
            evidence.append(f"Behavioral: Risk score {behavioral_result.risk_score:.2f}")
            active_methods += settings.BEHAVIORAL_CONFIDENCE_WEIGHT
        
        # Normalize confidence
        final_confidence = total_confidence if active_methods == 0 else total_confidence
        
        # Determine if should block
        blocked = final_confidence >= settings.BLOCK_THRESHOLD
        
        # Determine risk level
        if final_confidence >= 0.9:
            risk_level = RiskLevel.CRITICAL
        elif final_confidence >= 0.7:
            risk_level = RiskLevel.HIGH
        elif final_confidence >= 0.4:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return DetectionResult(
            technique_id=technique_id,
            technique_name=technique_name,
            blocked=blocked,
            confidence=final_confidence,
            risk_level=risk_level,
            pattern_result=pattern_result,
            ml_result=ml_result,
            rule_result=rule_result,
            behavioral_result=behavioral_result,
            evidence=evidence,
            methods_triggered=methods_triggered,
            input_text=input_text,
            request_id=context.get("request_id"),
            user_id=context.get("user_id"),
            session_id=context.get("session_id")
        )
    
    def _create_error_result(
        self,
        technique_id: str,
        input_text: str,
        error_message: str
    ) -> DetectionResult:
        """Create error result when technique not found."""
        return DetectionResult(
            technique_id=technique_id,
            technique_name="Unknown",
            blocked=False,
            confidence=0.0,
            risk_level=RiskLevel.LOW,
            evidence=[error_message],
            methods_triggered=[],
            input_text=input_text
        )


# Global instance
_detection_engine = None


def get_detection_engine() -> DetectionEngine:
    """Get global detection engine instance."""
    global _detection_engine
    if _detection_engine is None:
        _detection_engine = DetectionEngine()
    return _detection_engine

