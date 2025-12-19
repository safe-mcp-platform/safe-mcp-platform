"""
SAFE-MCP Gateway Client
Stdio client that connects Claude Desktop to SAFE-MCP Gateway
"""

import sys
import json
import os
import httpx
from typing import Dict, Any, Optional
import structlog
import asyncio

logger = structlog.get_logger()


class GatewayClient:
    """
    MCP stdio client that proxies to SAFE-MCP Gateway
    
    This runs as an MCP server from Claude Desktop's perspective,
    but actually forwards all requests to the SAFE-MCP Gateway via HTTP.
    """
    
    def __init__(self):
        self.gateway_url = os.getenv(
            "SAFE_MCP_GATEWAY_URL",
            "http://localhost:5002"
        ).rstrip("/")
        
        self.api_key = os.getenv("SAFE_MCP_API_KEY")
        if not self.api_key:
            raise ValueError("SAFE_MCP_API_KEY environment variable required")
        
        self.client = httpx.AsyncClient(
            base_url=self.gateway_url,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info("Gateway client initialized", gateway=self.gateway_url)
    
    async def run(self):
        """
        Run stdio loop
        Reads JSON-RPC from stdin, forwards to gateway, writes response to stdout
        """
        try:
            while True:
                # Read request from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    logger.debug("Request received", method=request.get("method"))
                    
                    # Forward to gateway
                    response = await self.forward_request(request)
                    
                    # Write response to stdout
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    logger.error("Invalid JSON", error=str(e))
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()
                
                except Exception as e:
                    logger.error("Error processing request", error=str(e))
        
        finally:
            await self.client.aclose()
    
    async def forward_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Forward JSON-RPC request to gateway"""
        try:
            http_response = await self.client.post(
                "/mcp",
                json=request
            )
            http_response.raise_for_status()
            return http_response.json()
            
        except httpx.HTTPError as e:
            logger.error("HTTP error forwarding request", error=str(e))
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Gateway error: {str(e)}"
                }
            }


async def main():
    """Main entry point"""
    client = GatewayClient()
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())

