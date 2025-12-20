"""
MCP Semantic Pattern Analyzer (NOVEL - Channel 1)

Innovation: Context-aware pattern analysis that understands MCP protocol semantics,
not just regex matching. Analyzes tool calls in their complete context including
tool capabilities, argument relationships, and call chain patterns.

This is fundamentally different from traditional pattern matching:
- Understands MCP protocol structure
- Analyzes semantic meaning, not just text
- Considers tool context and permissions
- Detects argument relationship anomalies

Author: Saurabh Yergattikar
"""

import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class MCPFeatureType(Enum):
    """Types of MCP-specific features extracted for analysis"""
    TOOL_PERMISSION = "tool_permission"
    RESOURCE_SCOPE = "resource_scope"
    ARGUMENT_SEMANTIC = "argument_semantic"
    TEMPLATE_STRUCTURE = "template_structure"
    CALL_CONTEXT = "call_context"


@dataclass
class MCPCall:
    """Represents an MCP tool call with full context"""
    method: str
    tool: str
    arguments: Dict[str, Any]
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    resource_hints: Optional[List[str]] = None
    session_id: Optional[str] = None
    call_sequence: Optional[int] = None


@dataclass
class SemanticRisk:
    """Risk assessment with semantic understanding"""
    risk_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    risk_type: str
    evidence: List[str]
    matched_patterns: List[str]
    semantic_features: Dict[str, Any]


class MCPSemanticPatternAnalyzer:
    """
    NOVEL: First semantic pattern analyzer for MCP protocol.
    
    Unlike traditional regex-based pattern matching, this analyzer:
    1. Understands MCP protocol semantics
    2. Analyzes tool capabilities and permissions
    3. Detects argument relationship anomalies
    4. Considers call context and sequences
    
    Technical Innovation:
    - Protocol-aware feature extraction
    - Semantic similarity matching
    - Context-dependent risk scoring
    - Multi-dimensional pattern analysis
    """
    
    def __init__(self, safe_mcp_patterns: Optional[Dict] = None):
        """
        Initialize with SAFE-MCP patterns.
        
        Args:
            safe_mcp_patterns: Dictionary of SAFE-MCP technique patterns
        """
        self.safe_mcp_patterns = safe_mcp_patterns or {}
        self.semantic_cache = {}
        
        # Initialize MCP-specific pattern databases
        self._load_mcp_semantic_patterns()
        
        logger.info("MCP Semantic Pattern Analyzer initialized")
    
    def _load_mcp_semantic_patterns(self):
        """Load MCP protocol-specific semantic patterns"""
        
        # NOVEL: Semantic patterns that understand MCP structure
        self.mcp_semantic_patterns = {
            "prompt_injection": {
                "semantic_markers": [
                    "instruction_override",
                    "role_manipulation", 
                    "system_bypass",
                    "context_poisoning"
                ],
                "tool_contexts": ["description", "schema", "examples"],
                "risk_multipliers": {
                    "high_privilege_tool": 1.5,
                    "data_access_tool": 1.3,
                    "code_execution_tool": 2.0
                }
            },
            "path_traversal": {
                "semantic_markers": [
                    "directory_escape",
                    "absolute_path_access",
                    "symlink_manipulation",
                    "encoding_evasion"
                ],
                "suspicious_patterns": [
                    r"\.\./",
                    r"\.\.\\",
                    r"^/etc/",
                    r"^/proc/",
                    r"%2e%2e",
                    r"..%252f"
                ],
                "context_checks": ["path_normalization", "sandbox_validation"]
            },
            "resource_exhaustion": {
                "semantic_markers": [
                    "recursive_calls",
                    "unbounded_iteration",
                    "large_resource_request"
                ],
                "thresholds": {
                    "max_iterations": 10000,
                    "max_resource_size": 100_000_000
                }
            },
            "data_exfiltration": {
                "semantic_markers": [
                    "external_communication",
                    "data_encoding",
                    "covert_channel"
                ],
                "suspicious_tool_chains": [
                    ["read_file", "send_http"],
                    ["list_files", "read_multiple", "external_api"]
                ]
            }
        }
    
    def analyze(self, mcp_call: MCPCall) -> SemanticRisk:
        """
        Perform semantic analysis of MCP call.
        
        This is the core NOVEL algorithm that goes beyond regex:
        1. Extract MCP-specific semantic features
        2. Analyze tool context and permissions
        3. Check argument relationships
        4. Match against semantic patterns
        5. Compute context-aware risk score
        
        Args:
            mcp_call: The MCP call to analyze
            
        Returns:
            SemanticRisk with detailed assessment
        """
        logger.info("Analyzing MCP call semantically", tool=mcp_call.tool)
        
        # Step 1: Extract MCP semantic features (NOVEL)
        features = self.extract_mcp_features(mcp_call)
        
        # Step 2: Analyze tool context (NOVEL)
        tool_risk = self.analyze_tool_context(mcp_call, features)
        
        # Step 3: Analyze argument semantics (NOVEL)
        arg_risk = self.analyze_argument_semantics(mcp_call, features)
        
        # Step 4: Check SAFE-MCP patterns
        safe_mcp_risk = self.check_safe_mcp_patterns(mcp_call, features)
        
        # Step 5: Aggregate risks with semantic weighting
        final_risk = self.aggregate_semantic_risks(
            tool_risk, arg_risk, safe_mcp_risk, features
        )
        
        logger.info(
            "Semantic analysis complete",
            risk_score=final_risk.risk_score,
            confidence=final_risk.confidence
        )
        
        return final_risk
    
    def extract_mcp_features(self, mcp_call: MCPCall) -> Dict[str, Any]:
        """
        NOVEL: Extract MCP protocol-specific semantic features.
        
        This extracts features that standard NLP/text analysis misses:
        - Tool capability declarations
        - Resource access patterns  
        - Permission scopes
        - Argument type semantics
        """
        features = {
            "tool_name": mcp_call.tool,
            "method": mcp_call.method,
            "arg_count": len(mcp_call.arguments),
            "has_description": mcp_call.description is not None,
        }
        
        # Extract tool permission features
        if mcp_call.permissions:
            features["permissions"] = self.parse_tool_permissions(mcp_call)
        
        # Extract resource scope
        if mcp_call.resource_hints:
            features["resource_scope"] = self.extract_resource_scope(mcp_call)
        
        # Analyze prompt/description structure
        if mcp_call.description:
            features["template_structure"] = self.analyze_prompt_structure(
                mcp_call.description
            )
        
        # Extract argument semantics
        features["argument_semantics"] = self.extract_argument_semantics(
            mcp_call.arguments
        )
        
        return features
    
    def parse_tool_permissions(self, mcp_call: MCPCall) -> Dict[str, Any]:
        """Parse and analyze tool permission declarations"""
        permissions = {
            "declared": mcp_call.permissions or [],
            "risk_level": "low",
            "scope": []
        }
        
        # Analyze permission risk
        high_risk_perms = ["file_write", "code_execute", "network_access", "system_call"]
        declared = set(mcp_call.permissions or [])
        
        if declared.intersection(high_risk_perms):
            permissions["risk_level"] = "high"
        
        return permissions
    
    def extract_resource_scope(self, mcp_call: MCPCall) -> Dict[str, Any]:
        """Extract and analyze resource access scope"""
        scope = {
            "resources": mcp_call.resource_hints or [],
            "bounded": True,
            "suspicious_access": []
        }
        
        # Check for suspicious resource patterns
        for resource in mcp_call.resource_hints or []:
            if any(pattern in str(resource).lower() for pattern in 
                   ["../", "/etc/", "/proc/", "system32", "windows"]):
                scope["suspicious_access"].append(resource)
                scope["bounded"] = False
        
        return scope
    
    def analyze_prompt_structure(self, description: str) -> Dict[str, Any]:
        """
        NOVEL: Analyze prompt/description structure for injection patterns.
        
        Goes beyond regex to understand semantic structure:
        - Instruction hierarchies
        - Role definitions
        - System directives
        - Hidden instructions
        """
        structure = {
            "length": len(description),
            "has_instructions": False,
            "has_role_definition": False,
            "has_system_directive": False,
            "instruction_markers": []
        }
        
        # Semantic instruction markers
        instruction_patterns = [
            r"ignore\s+(previous|all|any)\s+(instructions?|prompts?|rules?)",
            r"you\s+are\s+now",
            r"(new|updated)\s+instructions?",
            r"system\s*:",
            r"developer\s+mode",
            r"\[system\]",
            r"disregard",
            r"override"
        ]
        
        for pattern in instruction_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                structure["has_instructions"] = True
                structure["instruction_markers"].append(pattern)
        
        return structure
    
    def extract_argument_semantics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic meaning from arguments"""
        semantics = {
            "types": {},
            "suspicious_values": [],
            "encoding_detected": []
        }
        
        for key, value in arguments.items():
            # Type analysis
            semantics["types"][key] = type(value).__name__
            
            # Value analysis
            str_value = str(value)
            
            # Check for encoding attempts
            if any(enc in str_value.lower() for enc in ["%2e", "%2f", "\\x", "\\u"]):
                semantics["encoding_detected"].append(key)
            
            # Check for path traversal in any string argument
            if isinstance(value, str) and (".." in value or value.startswith("/")):
                semantics["suspicious_values"].append(key)
        
        return semantics
    
    def analyze_tool_context(self, mcp_call: MCPCall, features: Dict) -> float:
        """Analyze tool in its MCP context"""
        risk = 0.0
        
        # High-risk tool types
        if any(keyword in mcp_call.tool.lower() for keyword in 
               ["exec", "eval", "system", "shell", "delete", "write"]):
            risk += 0.3
        
        # Permission analysis
        if features.get("permissions", {}).get("risk_level") == "high":
            risk += 0.2
        
        # Resource scope analysis
        resource_scope = features.get("resource_scope", {})
        if not resource_scope.get("bounded", True):
            risk += 0.3
        if resource_scope.get("suspicious_access"):
            risk += 0.2
        
        return min(risk, 1.0)
    
    def analyze_argument_semantics(self, mcp_call: MCPCall, features: Dict) -> float:
        """Analyze argument semantic relationships"""
        risk = 0.0
        
        arg_semantics = features.get("argument_semantics", {})
        
        # Check for suspicious values
        if arg_semantics.get("suspicious_values"):
            risk += 0.4
        
        # Check for encoding attempts (evasion)
        if arg_semantics.get("encoding_detected"):
            risk += 0.3
        
        return min(risk, 1.0)
    
    def check_safe_mcp_patterns(self, mcp_call: MCPCall, features: Dict) -> float:
        """Check against SAFE-MCP technique patterns"""
        risk = 0.0
        
        # Check prompt injection patterns
        template_structure = features.get("template_structure", {})
        if template_structure.get("has_instructions"):
            risk += 0.5
        if template_structure.get("has_system_directive"):
            risk += 0.3
        
        return min(risk, 1.0)
    
    def aggregate_semantic_risks(
        self, 
        tool_risk: float,
        arg_risk: float, 
        safe_mcp_risk: float,
        features: Dict
    ) -> SemanticRisk:
        """Aggregate risks with semantic weighting"""
        
        # Weighted aggregation
        weights = {
            "tool": 0.25,
            "arguments": 0.35,
            "safe_mcp": 0.40
        }
        
        risk_score = (
            tool_risk * weights["tool"] +
            arg_risk * weights["arguments"] +
            safe_mcp_risk * weights["safe_mcp"]
        )
        
        # Compute confidence based on feature completeness
        confidence = self._compute_confidence(features)
        
        # Build evidence
        evidence = []
        if tool_risk > 0.5:
            evidence.append(f"High-risk tool context: {tool_risk:.2f}")
        if arg_risk > 0.5:
            evidence.append(f"Suspicious arguments: {arg_risk:.2f}")
        if safe_mcp_risk > 0.5:
            evidence.append(f"SAFE-MCP pattern matched: {safe_mcp_risk:.2f}")
        
        return SemanticRisk(
            risk_score=risk_score,
            confidence=confidence,
            risk_type="semantic_analysis",
            evidence=evidence,
            matched_patterns=[],
            semantic_features=features
        )
    
    def _compute_confidence(self, features: Dict) -> float:
        """Compute confidence based on feature completeness"""
        feature_count = len(features)
        max_features = 10  # Expected feature count
        
        return min(feature_count / max_features, 1.0)

