"""
Security exceptions for safe-mcp-sdk
"""

class SAFEMCPException(Exception):
    """Raised when a security violation is detected"""
    
    def __init__(
        self,
        technique_id: str,
        message: str,
        severity: str,
        evidence: list = None,
        parameter: str = None
    ):
        self.technique_id = technique_id
        self.message = message
        self.severity = severity
        self.evidence = evidence or []
        self.parameter = parameter
        
        full_message = (
            f"\n{'='*60}\n"
            f"🚨 SAFE-MCP Security Violation Detected!\n"
            f"{'='*60}\n"
            f"Technique ID: {technique_id}\n"
            f"Severity:     {severity}\n"
            f"Parameter:    {parameter or 'N/A'}\n"
            f"Message:      {message}\n"
            f"Evidence:     {', '.join(str(e) for e in evidence)}\n"
            f"{'='*60}\n"
        )
        super().__init__(full_message)

