"""
SAFE-MCP Validators - Uses same techniques as safe-mcp-platform
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional

class SAFEMCPValidator:
    """
    Validates inputs against SAFE-MCP threat techniques.
    Uses the SAME detection logic as safe-mcp-platform for consistency.
    """
    
    def __init__(self):
        self.techniques = {}
        self.patterns_cache = {}
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
                "parameter": str
            }
        """
        
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
                    "parameter": context.get("parameter") if context else None
                }
        
        # All checks passed
        return {
            "valid": True,
            "blocked": False,
            "message": "Input validated successfully"
        }
    
    def validate_all_techniques(self, input_text: str) -> Dict:
        """Validate against all loaded SAFE-MCP techniques"""
        return self.validate(input_text, techniques=None)

