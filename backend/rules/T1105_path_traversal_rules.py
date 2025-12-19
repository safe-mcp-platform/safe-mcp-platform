"""
SAFE-T1105: Path Traversal Detection Rules
Validates file paths for traversal attempts
"""

import os
import re
from typing import Dict, Any
from pathlib import Path
from utils.types import RuleResult

# Sensitive file patterns (commonly targeted)
SENSITIVE_FILES = [
    r'/etc/passwd$',
    r'/etc/shadow$',
    r'/\.ssh/id_rsa$',
    r'/\.ssh/authorized_keys$',
    r'/\.env$',
    r'/config/database\.(yml|yaml|json)$',
    r'/\.aws/credentials$',
    r'system32/config/sam$',
    r'/proc/self/environ$'
]

# Allowed base paths (sandbox directories)
ALLOWED_BASE_PATHS = [
    "/workspace",
    "/tmp/mcp-safe",
    "./data",
    "./workspace",
    "workspace",
    "data",
    "uploads",
    "downloads",
    "documents"
]


def validate_file_path(input_text: str, context: Dict[str, Any] = None) -> RuleResult:
    """
    Validate file path for traversal attempts.
    
    Args:
        input_text: File path to validate
        context: Additional context (base_path, etc.)
    
    Returns:
        RuleResult with validation outcome
    """
    risk_score = 0.0
    reasons = []
    rules_violated = []
    
    path = input_text.strip()
    
    # Rule 1: Check for basic traversal sequences
    traversal_patterns = [
        (r'\.\./|\.\.\\', "Unix/Windows traversal sequence"),
        (r'\.\.//|\.\.\\\\', "Double-slash traversal"),
        (r'\.\.;', "Semicolon traversal"),
        (r'%2e%2e', "URL-encoded traversal"),
        (r'%252e', "Double URL-encoded traversal"),
        (r'․․', "Unicode dot traversal"),
        (r'\.\u002e', "Unicode-encoded traversal")
    ]
    
    for pattern, description in traversal_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            risk_score += 0.4
            rules_violated.append("traversal_sequence")
            reasons.append(f"Detected: {description}")
            break  # Only count once for traversal
    
    # Rule 2: Check for absolute paths (should be relative)
    if os.path.isabs(path):
        risk_score += 0.3
        rules_violated.append("absolute_path")
        reasons.append("Absolute path not allowed")
    
    # Rule 3: Check for null byte injection
    if '\x00' in path or '%00' in path.lower():
        risk_score += 0.5
        rules_violated.append("null_byte")
        reasons.append("Null byte injection detected")
    
    # Rule 4: Normalize and check sandbox boundary
    try:
        normalized = os.path.normpath(path)
        
        # Check if normalized path goes outside sandbox
        if normalized.startswith('..') or '/..' in normalized or '\\..' in normalized:
            risk_score += 0.4
            rules_violated.append("sandbox_escape")
            reasons.append("Path escapes sandbox boundary")
        
        # If absolute after normalization, check against sensitive paths
        if os.path.isabs(normalized):
            for sensitive_pattern in SENSITIVE_FILES:
                if re.search(sensitive_pattern, normalized, re.IGNORECASE):
                    risk_score += 0.5
                    rules_violated.append("sensitive_file")
                    reasons.append(f"Targeting sensitive file: {normalized}")
                    break
    except Exception:
        pass  # If normalization fails, path is likely malicious anyway
    
    # Rule 5: Check for file:// protocol
    if path.lower().startswith('file://'):
        risk_score += 0.4
        rules_violated.append("file_protocol")
        reasons.append("File protocol URI detected")
    
    # Rule 6: Check for UNC paths (Windows)
    if path.startswith('\\\\') or re.match(r'^\\\\[\?\\.\\]', path):
        risk_score += 0.4
        rules_violated.append("unc_path")
        reasons.append("UNC path detected")
    
    # Rule 7: Check for tilde expansion
    if path.startswith('~') and '..' in path:
        risk_score += 0.3
        rules_violated.append("tilde_traversal")
        reasons.append("Tilde expansion with traversal")
    
    # Rule 8: Check depth (too many directory levels)
    depth = path.count('/') + path.count('\\')
    if depth > 10:
        risk_score += 0.2
        rules_violated.append("excessive_depth")
        reasons.append(f"Excessive directory depth ({depth} levels)")
    
    # Rule 9: Check if path starts with allowed base (whitelist validation)
    if not any(path.startswith(base) or path.startswith(f"./{base}") for base in ALLOWED_BASE_PATHS):
        # Only add risk if path doesn't look like a relative safe path
        if not path.startswith('./') or '..' in path:
            risk_score += 0.2
            rules_violated.append("non_whitelisted_base")
            reasons.append("Path not in allowed directories")
    
    # Rule 10: Check for encoding obfuscation
    encoding_patterns = [
        (r'%c0%af', "UTF-8 overlong encoding"),
        (r'%c1%9c', "UTF-8 overlong encoding"),
        (r'\\x2e\\x2e', "Hex encoding")
    ]
    
    for pattern, description in encoding_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            risk_score += 0.3
            rules_violated.append("encoding_obfuscation")
            reasons.append(f"Detected: {description}")
            break
    
    # Rule 11: Check for Windows drive letter traversal
    if re.search(r'[a-zA-Z]:\\', path):
        risk_score += 0.3
        rules_violated.append("windows_drive")
        reasons.append("Windows drive letter detected")
    
    # Rule 12: Check for path containing system directories
    dangerous_dirs = [
        '/etc/', '/root/', '/sys/', '/proc/',
        'C:\\Windows\\', 'C:\\Program Files\\'
    ]
    for dangerous_dir in dangerous_dirs:
        if dangerous_dir.lower() in path.lower():
            risk_score += 0.4
            rules_violated.append("system_directory")
            reasons.append(f"System directory access: {dangerous_dir}")
            break
    
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
validate = validate_file_path

