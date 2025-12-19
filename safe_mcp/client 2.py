"""
SAFE-MCP Client
Direct API client for detection service
"""

import httpx
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class SafeMCPClient:
    """Client for SAFE-MCP Detection API"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:5001",
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def check_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        technique_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check a tool call for security issues
        
        Args:
            tool_name: Name of the MCP tool
            arguments: Tool arguments
            technique_id: Specific technique to check (optional)
        
        Returns:
            Detection result with blocked flag, confidence, etc.
        """
        payload = {
            "tool": tool_name,
            "arguments": arguments
        }
        
        if technique_id:
            payload["technique_id"] = technique_id
        
        response = await self.client.post("/v1/detect", json=payload)
        response.raise_for_status()
        
        return response.json()
    
    async def check_text(
        self,
        text: str,
        technique_id: str = "SAFE-T1102",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check text for security issues
        
        Args:
            text: Text to check
            technique_id: Technique ID to check
            context: Additional context
        
        Returns:
            Detection result
        """
        payload = {
            "input_text": text,
            "technique_id": technique_id
        }
        
        if context:
            payload["context"] = context
        
        response = await self.client.post("/v1/detect", json=payload)
        response.raise_for_status()
        
        return response.json()
    
    async def health(self) -> Dict[str, Any]:
        """Check service health"""
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

