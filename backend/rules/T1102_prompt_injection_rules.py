"""
SAFE-T1102: Prompt Injection Detection Rules
Validates tool descriptions for malicious prompt injection attempts
"""

import re
from typing import Dict, Any
from utils.types import RuleResult

# Dangerous keywords that indicate instruction override
INSTRUCTION_OVERRIDE_KEYWORDS = [
    "ignore", "disregard", "forget", "override",
    "previous instructions", "system prompt", "new instructions"
]

# Role manipulation indicators
ROLE_MANIPULATION_KEYWORDS = [
    "you are now", "act as", "pretend to be",
    "roleplay", "DAN", "developer mode", "god mode"
]

# System prompt bypass indicators
SYSTEM_BYPASS_PATTERNS = [
    r"\[SYSTEM\]",
    r"<system>",
    r"\*\*system\*\*:",
    r"system:",
    r"new system prompt"
]

# Safety override indicators
SAFETY_OVERRIDE_KEYWORDS = [
    "disable safety", "turn off safety", "bypass restrictions",
    "no restrictions", "unlimited access", "remove filters",
    "disable guardrails", "bypass security"
]


def validate_tool_description(input_text: str, context: Dict[str, Any] = None) -> RuleResult:
    """
    Validate tool description for prompt injection attempts.
    
    Args:
        input_text: Tool description text
        context: Additional context
    
    Returns:
        RuleResult with validation outcome
    """
    risk_score = 0.0
    reasons = []
    rules_violated = []
    
    text_lower = input_text.lower()
    
    # Rule 1: Check for instruction override
    override_count = 0
    for keyword in INSTRUCTION_OVERRIDE_KEYWORDS:
        if keyword in text_lower:
            override_count += 1
            risk_score += 0.15
    
    if override_count > 0:
        rules_violated.append("instruction_override")
        reasons.append(f"Instruction override keywords detected ({override_count} instances)")
    
    # Rule 2: Check for role manipulation
    role_manip_count = 0
    for keyword in ROLE_MANIPULATION_KEYWORDS:
        if keyword in text_lower:
            role_manip_count += 1
            risk_score += 0.15
    
    if role_manip_count > 0:
        rules_violated.append("role_manipulation")
        reasons.append(f"Role manipulation detected ({role_manip_count} instances)")
    
    # Rule 3: Check for system prompt bypass
    system_bypass_count = 0
    for pattern in SYSTEM_BYPASS_PATTERNS:
        if re.search(pattern, input_text, re.IGNORECASE):
            system_bypass_count += 1
            risk_score += 0.2
    
    if system_bypass_count > 0:
        rules_violated.append("system_bypass")
        reasons.append("System prompt bypass patterns detected")
    
    # Rule 4: Check for safety override
    safety_override_count = 0
    for keyword in SAFETY_OVERRIDE_KEYWORDS:
        if keyword in text_lower:
            safety_override_count += 1
            risk_score += 0.2
    
    if safety_override_count > 0:
        rules_violated.append("safety_override")
        reasons.append(f"Safety override keywords detected ({safety_override_count} instances)")
    
    # Rule 5: Check for multiple instruction verbs in short text
    instruction_verbs = ["must", "should", "will", "can", "shall", "need to"]
    verb_count = sum(1 for verb in instruction_verbs if verb in text_lower)
    if len(input_text) < 200 and verb_count >= 4:
        risk_score += 0.15
        rules_violated.append("excessive_instructions")
        reasons.append(f"Excessive instruction verbs in short text ({verb_count} verbs)")
    
    # Rule 6: Check for hidden instructions (comments, special formatting)
    if re.search(r'<!--.*?-->', input_text, re.DOTALL):
        risk_score += 0.1
        rules_violated.append("hidden_instructions")
        reasons.append("HTML comments detected (potential hidden instructions)")
    
    if re.search(r'\[hidden.*?\]', input_text, re.IGNORECASE):
        risk_score += 0.15
        rules_violated.append("hidden_instructions")
        reasons.append("Hidden instruction markers detected")
    
    # Rule 7: Check for obfuscation attempts (1337 speak, unicode)
    if re.search(r'[i1!][gq][n][o0][r][e3]', text_lower):  # ign0re variants
        risk_score += 0.1
        rules_violated.append("obfuscation")
        reasons.append("Text obfuscation detected")
    
    # Rule 8: Check for meta-instructions (instructions about instructions)
    meta_patterns = [
        "from now on", "starting now", "beginning now",
        "reset your", "clear your", "new persona"
    ]
    meta_count = sum(1 for pattern in meta_patterns if pattern in text_lower)
    if meta_count > 0:
        risk_score += 0.2 * meta_count
        rules_violated.append("meta_instructions")
        reasons.append(f"Meta-instructions detected ({meta_count} instances)")
    
    # Cap risk score at 1.0
    risk_score = min(risk_score, 1.0)
    
    # Determine if should trigger (threshold 0.7)
    triggered = risk_score >= 0.7
    
    return RuleResult(
        triggered=triggered,
        confidence=risk_score,
        rules_violated=rules_violated,
        reasons=reasons
    )


# Alias for dynamic loading
validate = validate_tool_description

