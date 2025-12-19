"""
Dynamic Detection Engine - The Heart of SAFE-MCP Platform

This engine dynamically loads and executes SAFE-T techniques from configuration files.
NO HARDCODED DETECTION LOGIC - Everything is data-driven!

Key Innovation: Add new attack technique = Just drop a JSON file. No code changes!
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from config import settings


@dataclass
class DetectionResult:
    """Single detection result"""
    technique_id: str
    technique_name: str
    matched: bool
    confidence: float
    evidence: List[str]
    method: str  # pattern, ml_model, behavioral, rule
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    tactic: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "technique_id": self.technique_id,
            "technique_name": self.technique_name,
            "matched": self.matched,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "method": self.method,
            "severity": self.severity,
            "tactic": self.tactic,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AggregatedDetectionResult:
    """Aggregated results from all detectors"""
    overall_risk_level: str  # CRITICAL, HIGH, MEDIUM, LOW, NONE
    matched_techniques: List[DetectionResult]
    action: str  # BLOCK, ALLOW, LOG
    confidence: float
    mitigations: List[str]  # SAFE-M IDs to apply
    
    def to_dict(self) -> dict:
        return {
            "overall_risk_level": self.overall_risk_level,
            "matched_techniques": [t.to_dict() for t in self.matched_techniques],
            "action": self.action,
            "confidence": self.confidence,
            "mitigations": self.mitigations,
            "detection_count": len(self.matched_techniques)
        }


class DynamicDetectionEngine:
    """
    Generic detection engine that auto-loads ALL techniques from config files.
    
    Architecture:
    - Scans techniques directory at startup
    - Creates generic detector for each technique
    - Runs all detectors in parallel
    - Aggregates results and determines action
    
    NO hardcoded technique logic - everything is data-driven!
    """
    
    def __init__(self):
        self.techniques: Dict[str, dict] = {}
        self.detectors: Dict[str, 'GenericDetector'] = {}
        self.mitigations: Dict[str, dict] = {}
        self.ml_model_loader = None  # Lazy-loaded
        
        # Load all techniques from config files
        if settings.auto_load_techniques:
            self.load_all_techniques()
        
        # Load mitigations
        if settings.auto_load_mitigations:
            self.load_all_mitigations()
    
    def load_all_techniques(self):
        """
        Auto-discover and load all SAFE-T technique configurations.
        
        This method scans the techniques directory and creates a detector
        for each technique - NO hardcoding required!
        """
        techniques_dir = Path(settings.safe_mcp_data_dir) / "techniques"
        
        if not techniques_dir.exists():
            print(f"⚠️  Techniques directory not found: {techniques_dir}")
            print(f"   Creating directory and loading sample techniques...")
            techniques_dir.mkdir(parents=True, exist_ok=True)
            self._create_sample_techniques(techniques_dir)
            return
        
        print(f"📁 Loading techniques from: {techniques_dir}")
        
        # Load individual technique files
        for config_file in techniques_dir.glob("SAFE-T*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    technique_config = json.load(f)
                
                technique_id = technique_config["id"]
                self.techniques[technique_id] = technique_config
                
                # Create detector instance
                detector = self._create_detector(technique_config)
                self.detectors[technique_id] = detector
                
                print(f"✅ Loaded: {technique_id} - {technique_config['name']}")
            
            except Exception as e:
                print(f"⚠️  Error loading {config_file.name}: {e}")
        
        print(f"✨ Total techniques loaded: {len(self.techniques)}")
    
    def _create_detector(self, config: dict) -> 'GenericDetector':
        """Factory method: Create generic detector from config"""
        from detectors.generic_detector import GenericDetector
        return GenericDetector(config, self)
    
    def load_all_mitigations(self):
        """Load all SAFE-M mitigation configurations"""
        mitigations_file = Path(settings.safe_mcp_data_dir) / "mitigations.json"
        
        if not mitigations_file.exists():
            print(f"⚠️  Mitigations file not found: {mitigations_file}")
            return
        
        try:
            with open(mitigations_file, 'r', encoding='utf-8') as f:
                self.mitigations = json.load(f)
            print(f"✅ Loaded {len(self.mitigations)} mitigations")
        except Exception as e:
            print(f"⚠️  Error loading mitigations: {e}")
    
    async def detect_all(
        self,
        mcp_message: Any,
        session_context: Optional[Any] = None
    ) -> AggregatedDetectionResult:
        """
        Run ALL enabled detectors in parallel.
        
        This is the main detection entry point - automatically scales with
        the number of techniques without code changes!
        
        Args:
            mcp_message: The MCP message to analyze
            session_context: Optional session context for behavioral analysis
        
        Returns:
            AggregatedDetectionResult with all matched techniques
        """
        # Filter enabled techniques
        enabled_techniques = {
            tid: det 
            for tid, det in self.detectors.items()
            if self.techniques[tid].get("enabled", True)
        }
        
        if not enabled_techniques:
            return AggregatedDetectionResult(
                overall_risk_level="NONE",
                matched_techniques=[],
                action="ALLOW",
                confidence=1.0,
                mitigations=[]
            )
        
        print(f"🔍 Running {len(enabled_techniques)} detectors in parallel...")
        
        # Run all detectors in parallel (async)
        tasks = [
            detector.detect(mcp_message, session_context)
            for detector in enabled_techniques.values()
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print(f"⚠️  Error in parallel detection: {e}")
            results = []
        
        # Filter matches
        matches = [
            r for r in results 
            if isinstance(r, DetectionResult) and r.matched
        ]
        
        # Aggregate results
        return self._aggregate_results(matches)
    
    def _aggregate_results(self, matches: List[DetectionResult]) -> AggregatedDetectionResult:
        """
        Aggregate multiple detection results into a single decision.
        
        Logic:
        - Overall risk = highest individual risk
        - Action = based on risk level and policy
        - Mitigations = all recommended mitigations
        """
        if not matches:
            return AggregatedDetectionResult(
                overall_risk_level="NONE",
                matched_techniques=[],
                action="ALLOW",
                confidence=1.0,
                mitigations=[]
            )
        
        # Determine overall risk (highest severity)
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
        max_severity = max(matches, key=lambda m: severity_order.get(m.severity, 0))
        overall_risk = max_severity.severity
        
        # Determine action
        if overall_risk in ["CRITICAL", "HIGH"]:
            action = "BLOCK"
        elif overall_risk == "MEDIUM":
            action = "LOG"  # Or BLOCK based on policy
        else:
            action = "ALLOW"
        
        # Calculate confidence (average of all matches)
        avg_confidence = sum(m.confidence for m in matches) / len(matches)
        
        # Collect mitigations
        mitigations = []
        for match in matches:
            technique_config = self.techniques.get(match.technique_id, {})
            mitigations.extend(technique_config.get("mitigations", []))
        mitigations = list(set(mitigations))  # Deduplicate
        
        return AggregatedDetectionResult(
            overall_risk_level=overall_risk,
            matched_techniques=matches,
            action=action,
            confidence=avg_confidence,
            mitigations=mitigations
        )
    
    async def load_ml_model(self, model_id: str):
        """Lazy-load ML model when needed"""
        if self.ml_model_loader is None:
            from services.ml_model_loader import MLModelLoader
            self.ml_model_loader = MLModelLoader()
        
        return await self.ml_model_loader.load_model(model_id)
    
    def _create_sample_techniques(self, techniques_dir: Path):
        """Create sample technique configurations for demo"""
        samples = [
            {
                "id": "SAFE-T1001",
                "name": "Prompt Injection via MCP",
                "tactic": "Initial Access",
                "severity": "HIGH",
                "description": "Attacker manipulates MCP prompts to override system instructions",
                "mitigations": ["SAFE-M-1", "SAFE-M-2"],
                "enabled": True,
                "detection": {
                    "method": "hybrid",
                    "patterns": [
                        {
                            "type": "substring",
                            "pattern": "ignore previous instructions",
                            "case_sensitive": False,
                            "weight": 0.9
                        },
                        {
                            "type": "substring",
                            "pattern": "disregard system prompt",
                            "case_sensitive": False,
                            "weight": 0.9
                        }
                    ]
                }
            },
            {
                "id": "SAFE-T1601",
                "name": "File System Discovery",
                "tactic": "Discovery",
                "severity": "MEDIUM",
                "description": "Unauthorized filesystem enumeration via MCP tools",
                "mitigations": ["SAFE-M-12"],
                "enabled": True,
                "detection": {
                    "method": "rule",
                    "rules": [
                        {
                            "type": "path_check",
                            "check": "sensitive_path",
                            "patterns": ["/etc/passwd", "/etc/shadow", "C:\\Windows\\System32"]
                        }
                    ]
                }
            }
        ]
        
        for sample in samples:
            file_path = techniques_dir / f"{sample['id']}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sample, f, indent=2)
            print(f"📝 Created sample: {sample['id']}")


# Global instance
detection_engine = DynamicDetectionEngine()

