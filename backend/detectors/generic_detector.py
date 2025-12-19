"""
Generic Detector - Universal detector for ALL SAFE-T techniques

This single class can execute ANY technique based on its configuration.
NO technique-specific code - everything is data-driven!

Key Innovation: One detector class runs 80+ techniques!
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime


class GenericDetector:
    """
    Universal detector that executes ANY technique based on configuration.
    
    Supports 4 detection methods:
    1. Pattern matching (regex/substring)
    2. ML model inference
    3. Behavioral analysis
    4. Rule-based logic
    
    Configuration-driven - no hardcoded technique logic!
    """
    
    def __init__(self, config: dict, engine: Any):
        self.config = config
        self.technique_id = config["id"]
        self.technique_name = config["name"]
        self.severity = config.get("severity", "MEDIUM")
        self.tactic = config.get("tactic", "Unknown")
        self.engine = engine
        
        # Pre-compile patterns for performance
        self.compiled_patterns = self._compile_patterns()
        
        # Lazy-load ML model
        self._ml_model = None
    
    async def detect(
        self,
        mcp_message: Any,
        session_context: Optional[Any] = None
    ) -> 'DetectionResult':
        """
        Execute detection using configured methods.
        
        All logic is driven by config - no hardcoded technique logic!
        
        Args:
            mcp_message: MCP message to analyze
            session_context: Optional session context for behavioral analysis
        
        Returns:
            DetectionResult with match status and evidence
        """
        from services.dynamic_detection_engine import DetectionResult
        
        detection_config = self.config.get("detection", {})
        method = detection_config.get("method", "pattern")
        
        scores = []
        evidence = []
        
        # Run pattern detection if configured
        if "patterns" in detection_config and detection_config.get("patterns"):
            pattern_result = await self._detect_patterns(mcp_message, detection_config["patterns"])
            if pattern_result["matched"]:
                scores.append(pattern_result["score"])
                evidence.extend(pattern_result["evidence"])
        
        # Run ML detection if configured
        ml_config = detection_config.get("ml_model", {})
        if ml_config.get("enabled", False):
            ml_result = await self._detect_ml(mcp_message, ml_config)
            if ml_result["matched"]:
                scores.append(ml_result["score"])
                evidence.append(ml_result["evidence"])
        
        # Run behavioral detection if configured
        behavioral_config = detection_config.get("behavioral", {})
        if behavioral_config.get("enabled", False) and session_context:
            behavioral_result = await self._detect_behavioral(mcp_message, behavioral_config, session_context)
            if behavioral_result["matched"]:
                scores.append(behavioral_result["score"])
                evidence.extend(behavioral_result["evidence"])
        
        # Run rule-based detection if configured
        if "rules" in detection_config and detection_config.get("rules"):
            rule_result = await self._detect_rules(mcp_message, detection_config["rules"])
            if rule_result["matched"]:
                scores.append(rule_result["score"])
                evidence.extend(rule_result["evidence"])
        
        # Aggregate results
        if scores:
            final_score = max(scores)  # Use highest confidence
            return DetectionResult(
                technique_id=self.technique_id,
                technique_name=self.technique_name,
                matched=True,
                confidence=final_score,
                evidence=evidence,
                method=method,
                severity=self.severity,
                tactic=self.tactic
            )
        
        return DetectionResult(
            technique_id=self.technique_id,
            technique_name=self.technique_name,
            matched=False,
            confidence=0.0,
            evidence=[],
            method=method,
            severity=self.severity,
            tactic=self.tactic
        )
    
    async def _detect_patterns(self, msg: Any, patterns_config: List[dict]) -> dict:
        """
        Generic pattern matching - works for ANY technique.
        
        Supports:
        - Regex patterns
        - Substring matching
        - Case-sensitive/insensitive
        """
        text = self._extract_text(msg)
        matches = []
        max_score = 0.0
        
        for pattern_def in patterns_config:
            pattern_type = pattern_def.get("type", "substring")
            pattern = pattern_def.get("pattern", "")
            weight = pattern_def.get("weight", 1.0)
            
            if pattern_type == "regex":
                regex = self.compiled_patterns.get(pattern)
                if regex and regex.search(text):
                    matches.append(f"Matched regex: {pattern}")
                    max_score = max(max_score, weight)
            
            elif pattern_type == "substring":
                case_sensitive = pattern_def.get("case_sensitive", False)
                if case_sensitive:
                    if pattern in text:
                        matches.append(f"Found substring: {pattern}")
                        max_score = max(max_score, weight)
                else:
                    if pattern.lower() in text.lower():
                        matches.append(f"Found substring (case-insensitive): {pattern}")
                        max_score = max(max_score, weight)
        
        return {
            "matched": len(matches) > 0,
            "score": max_score,
            "evidence": matches
        }
    
    async def _detect_ml(self, msg: Any, ml_config: dict) -> dict:
        """
        Generic ML detection - works for ANY HuggingFace model.
        
        Lazy-loads the model specified in config and runs inference.
        """
        model_id = ml_config.get("model_id", "")
        threshold = ml_config.get("threshold", 0.75)
        
        if not model_id:
            return {"matched": False}
        
        try:
            # Lazy-load model
            if self._ml_model is None:
                self._ml_model = await self.engine.load_ml_model(model_id)
            
            # Format input for model
            input_text = self._format_for_ml(msg)
            
            # Run inference
            prediction = await self._ml_model.predict(input_text)
            
            if prediction.get("is_attack", False) and prediction.get("confidence", 0) >= threshold:
                return {
                    "matched": True,
                    "score": prediction["confidence"],
                    "evidence": f"ML model {model_id} detected attack (confidence: {prediction['confidence']:.2f})"
                }
        
        except Exception as e:
            print(f"⚠️  ML detection error for {self.technique_id}: {e}")
        
        return {"matched": False}
    
    async def _detect_behavioral(self, msg: Any, behavioral_config: dict, session_ctx: Any) -> dict:
        """
        Generic behavioral detection - analyzes patterns over time.
        
        Checks for anomalies, rate spikes, unusual patterns.
        """
        matches = []
        max_score = 0.0
        
        rules = behavioral_config.get("rules", [])
        
        for rule in rules:
            feature = rule.get("feature", "")
            check = rule.get("check", "")
            threshold = rule.get("threshold", 0.0)
            
            # Dynamic feature extraction
            if feature == "request_rate":
                # Check request rate anomaly
                if hasattr(session_ctx, 'request_rate'):
                    if session_ctx.request_rate > threshold:
                        matches.append(f"High request rate: {session_ctx.request_rate} > {threshold}")
                        max_score = max(max_score, 0.8)
            
            elif feature == "encoding_anomaly":
                # Check for encoding tricks
                score = self._check_encoding_anomaly(msg, check)
                if score > threshold:
                    matches.append(f"Encoding anomaly detected: {check}")
                    max_score = max(max_score, score)
        
        return {
            "matched": len(matches) > 0,
            "score": max_score,
            "evidence": matches
        }
    
    async def _detect_rules(self, msg: Any, rules_config: List[dict]) -> dict:
        """
        Generic rule evaluation - checks structural/protocol violations.
        
        Can evaluate any rule based on MCP message properties.
        """
        matches = []
        
        for rule in rules_config:
            rule_type = rule.get("type", "")
            check = rule.get("check", "")
            patterns = rule.get("patterns", [])
            
            # Evaluate rule based on type
            if rule_type == "path_check":
                # Check for sensitive paths
                path = self._extract_path(msg)
                if path and patterns:
                    for pattern in patterns:
                        if pattern in path:
                            matches.append(f"Sensitive path access: {pattern}")
            
            elif rule_type == "mcp_structure":
                # Check MCP message structure
                if self._evaluate_structure_rule(msg, check):
                    matches.append(f"MCP structure violation: {check}")
        
        return {
            "matched": len(matches) > 0,
            "score": 1.0 if matches else 0.0,
            "evidence": matches
        }
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Pre-compile regex patterns for performance"""
        compiled = {}
        detection_config = self.config.get("detection", {})
        patterns_config = detection_config.get("patterns", [])
        
        for pattern_def in patterns_config:
            if pattern_def.get("type") == "regex":
                pattern = pattern_def.get("pattern", "")
                if pattern:
                    flags = 0 if pattern_def.get("case_sensitive", False) else re.IGNORECASE
                    try:
                        compiled[pattern] = re.compile(pattern, flags)
                    except re.error as e:
                        print(f"⚠️  Invalid regex in {self.technique_id}: {pattern} - {e}")
        
        return compiled
    
    def _extract_text(self, msg: Any) -> str:
        """Extract all text content from MCP message"""
        if isinstance(msg, str):
            return msg
        
        if isinstance(msg, dict):
            # Extract from common MCP fields
            text_parts = []
            
            # Tool arguments
            if "arguments" in msg:
                text_parts.append(str(msg["arguments"]))
            
            # Content field
            if "content" in msg:
                text_parts.append(str(msg["content"]))
            
            # Prompt field
            if "prompt" in msg:
                text_parts.append(str(msg["prompt"]))
            
            # Recursively extract from nested dicts
            for value in msg.values():
                if isinstance(value, (str, dict)):
                    text_parts.append(self._extract_text(value))
            
            return " ".join(text_parts)
        
        return str(msg)
    
    def _extract_path(self, msg: Any) -> Optional[str]:
        """Extract file path from MCP message"""
        if isinstance(msg, dict):
            # Check common path fields
            for key in ["path", "file", "filename", "filepath", "directory"]:
                if key in msg:
                    return str(msg[key])
            
            # Check in arguments
            if "arguments" in msg and isinstance(msg["arguments"], dict):
                return self._extract_path(msg["arguments"])
        
        return None
    
    def _format_for_ml(self, msg: Any) -> str:
        """Format MCP message for ML model input"""
        if isinstance(msg, dict):
            # Create structured input
            parts = []
            
            if "method" in msg:
                parts.append(f"Method: {msg['method']}")
            
            if "params" in msg:
                params = msg["params"]
                if "name" in params:
                    parts.append(f"Tool: {params['name']}")
                if "arguments" in params:
                    parts.append(f"Arguments: {params['arguments']}")
            
            return " | ".join(parts) if parts else self._extract_text(msg)
        
        return str(msg)
    
    def _check_encoding_anomaly(self, msg: Any, check: str) -> float:
        """Check for encoding anomalies (unicode tricks, null bytes, etc.)"""
        text = self._extract_text(msg)
        
        if check == "unicode_homograph":
            # Check for lookalike characters
            non_ascii = sum(1 for c in text if ord(c) > 127)
            if len(text) > 0 and non_ascii / len(text) > 0.3:
                return 0.9
        
        elif check == "null_byte":
            if "\x00" in text:
                return 1.0
        
        return 0.0
    
    def _evaluate_structure_rule(self, msg: Any, check: str) -> bool:
        """Evaluate MCP message structure rules"""
        if not isinstance(msg, dict):
            return False
        
        if check == "validation":
            # Check if valid MCP message structure
            required_fields = ["jsonrpc", "method"]
            return not all(field in msg for field in required_fields)
        
        elif check == "tool_override_attempt":
            # Check for system override attempts
            text = self._extract_text(msg).lower()
            override_indicators = ["override", "bypass", "disable", "ignore system"]
            return any(indicator in text for indicator in override_indicators)
        
        return False

