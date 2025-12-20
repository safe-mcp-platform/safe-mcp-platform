"""
SAFE-MCP Validators - Uses novel detection engine when available

This validator can operate in two modes:
1. Full Engine Mode: Uses the novel 4-channel detection engine (when available)
2. Standalone Mode: Uses built-in pattern matching (for SDK-only deployments)
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional
import asyncio

class SAFEMCPValidator:
    """
    Validates inputs against SAFE-MCP threat techniques.
    
    Modes:
    - Full Engine: Uses novel 4-channel detection (best accuracy)
    - Standalone: Uses pattern matching (portable)
    """
    
    def __init__(self, use_full_engine: bool = True):
        self.techniques = {}
        self.patterns_cache = {}
        self.use_full_engine = use_full_engine
        self.detection_engine = None
        
        # Try to load full novel detection engine
        if use_full_engine:
            try:
                from engine.novel_detection_engine import create_novel_detection_engine
                self.detection_engine = create_novel_detection_engine()
            except ImportError:
                # Fall back to pattern-based
                self.use_full_engine = False
        
        self._load_techniques()
    
    def _load_techniques(self):
        """Load SAFE-MCP techniques from parent project"""
        # Try multiple paths
        possible_paths = [
            Path(__file__).parent.parent.parent / "backend" / "techniques",
            Path(__file__).parent.parent.parent.parent / "backend" / "techniques",
        ]
        
        techniques_dir = None
        for path in possible_paths:
            if path.exists():
                techniques_dir = path
                break
        
        if not techniques_dir:
            # Fallback to minimal built-in techniques
            self._load_builtin_techniques()
            return
        
        # Load all technique JSON files
        for tech_file in techniques_dir.glob("*.json"):
            try:
                with open(tech_file, 'r') as f:
                    data = json.load(f)
                    
                tid = data.get("id")
                if not tid:
                    continue
                    
                self.techniques[tid] = {
                    "name": data.get("name", "Unknown"),
                    "severity": data.get("severity", "MEDIUM"),
                    "patterns": []
                }
                
                # Extract patterns
                detection = data.get("detection", {})
                patterns_config = detection.get("patterns", {})
                if patterns_config.get("enabled"):
                    # Try to load from patterns file
                    patterns_file = patterns_config.get("file")
                    if patterns_file:
                        patterns_path = techniques_dir.parent / patterns_file
                        if patterns_path.exists():
                            with open(patterns_path, 'r') as pf:
                                patterns = [line.strip() for line in pf if line.strip() and not line.startswith('#')]
                                self.techniques[tid]["patterns"] = patterns
                    else:
                        self.techniques[tid]["patterns"] = patterns_config.get("items", [])
                
                # Pre-compile regex patterns
                self.patterns_cache[tid] = [
                    re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    for pattern in self.techniques[tid]["patterns"]
                ]
            except Exception as e:
                continue
    
    def _load_builtin_techniques(self):
        """Built-in techniques for standalone SDK"""
        self.techniques = {
            "SAFE-T1102": {
                "name": "Prompt Injection via Tool Descriptions",
                "severity": "HIGH",
                "patterns": [
                    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
                    r"disregard\s+(all\s+)?(previous|prior|above)",
                    r"forget\s+(all\s+)?(previous|prior|above)",
                    r"new\s+instructions?:",
                    r"system\s+prompt",
                    r"reveal.*secrets?",
                ]
            },
            "SAFE-T1105": {
                "name": "Path Traversal via File Access Tools",
                "severity": "CRITICAL",
                "patterns": [
                    r"\.\./\.\./",
                    r"\.\./\.\./\.\./",
                    r"\.\./\.\./\.\./\.\./",
                    r"\.\.\\\.\.\\",
                    r"%2e%2e%2f",
                    r"\.\.%2f",
                    r"/etc/passwd",
                    r"/etc/shadow",
                ]
            },
            "SAFE-T1103": {
                "name": "Command Injection via Shell Execution",
                "severity": "CRITICAL",
                "patterns": [
                    r";\s*rm\s",
                    r"\|\s*cat\s",
                    r"&&\s*wget\s",
                    r"&&\s*echo\s",
                    r"`.*`",
                    r"\$\(.*\)",
                    r"rm\s+-rf\s+/",
                ]
            }
        }
        
        # Pre-compile patterns
        for tid, tech in self.techniques.items():
            self.patterns_cache[tid] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in tech["patterns"]
            ]
    
    def validate(
        self,
        input_text: str,
        techniques: Optional[List[str]] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Validate input against SAFE-MCP techniques.
        
        Uses novel 4-channel detection engine if available,
        falls back to pattern matching otherwise.
        
        Returns:
            {
                "valid": bool,
                "blocked": bool,
                "technique_id": str,
                "technique_name": str,
                "message": str,
                "severity": str,
                "confidence": float,
                "evidence": list,
                "parameter": str,
                "detection_mode": str  # "full_engine" or "patterns"
            }
        """
        
        # Try full engine mode first
        if self.use_full_engine and self.detection_engine:
            return self._validate_with_engine(input_text, techniques, context)
        
        # Fall back to pattern-based validation
        return self._validate_with_patterns(input_text, techniques, context)
    
    def _validate_with_engine(
        self,
        input_text: str,
        techniques: Optional[List[str]],
        context: Optional[Dict]
    ) -> Dict:
        """Validate using novel 4-channel detection engine"""
        
        # Create MCP call structure
        mcp_call = {
            "tool": context.get("function", "unknown") if context else "unknown",
            "arguments": {
                context.get("parameter", "input") if context else "input": input_text
            },
            "description": input_text if len(input_text) < 200 else None
        }
        
        # Run detection
        try:
            result = asyncio.run(
                self.detection_engine.detect(
                    mcp_call,
                    technique_id=techniques[0] if techniques and len(techniques) > 0 else None
                )
            )
            
            return {
                "valid": not result.blocked,
                "blocked": result.blocked,
                "technique_id": result.technique_id,
                "technique_name": result.technique_name,
                "message": f"Detected {result.technique_name}" if result.blocked else "Validated",
                "severity": result.technique_id.split("-")[0] if result.technique_id else "UNKNOWN",
                "confidence": result.confidence,
                "evidence": result.evidence[:3],  # First 3
                "parameter": context.get("parameter") if context else None,
                "detection_mode": "full_engine",
                "risk_score": result.risk_score,
                "methods_triggered": result.methods_triggered
            }
        except Exception as e:
            # Fall back to patterns if engine fails
            return self._validate_with_patterns(input_text, techniques, context)
    
    def _validate_with_patterns(
        self,
        input_text: str,
        techniques: Optional[List[str]],
        context: Optional[Dict]
    ) -> Dict:
        """Validate using pattern matching (standalone mode)"""
        
        # Determine which techniques to check
        techniques_to_check = techniques if techniques else list(self.techniques.keys())
        
        # Check each technique
        for tid in techniques_to_check:
            if tid not in self.techniques:
                continue
            
            technique = self.techniques[tid]
            
            # Pattern matching
            patterns_matched = []
            for pattern_regex in self.patterns_cache.get(tid, []):
                match = pattern_regex.search(input_text)
                if match:
                    patterns_matched.append(pattern_regex.pattern)
            
            if patterns_matched:
                # Attack detected!
                confidence = min(len(patterns_matched) * 0.2, 1.0)
                
                return {
                    "valid": False,
                    "blocked": True,
                    "technique_id": tid,
                    "technique_name": technique["name"],
                    "message": f"Detected {technique['name']}",
                    "severity": technique["severity"],
                    "confidence": confidence,
                    "evidence": patterns_matched,
                    "parameter": context.get("parameter") if context else None,
                    "detection_mode": "patterns"
                }
        
        # All checks passed
        return {
            "valid": True,
            "blocked": False,
            "message": "Input validated successfully",
            "detection_mode": "patterns"
        }
    
    def validate_all_techniques(self, input_text: str) -> Dict:
        """Validate against all loaded SAFE-MCP techniques"""
        return self.validate(input_text, techniques=None)

