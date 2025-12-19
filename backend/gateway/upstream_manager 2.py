"""
Upstream Server Manager
Manages lifecycle of upstream MCP servers
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import structlog
import subprocess
from pathlib import Path

logger = structlog.get_logger()


@dataclass
class ServerConfig:
    """Configuration for an upstream MCP server"""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    enabled: bool = True


class UpstreamServer:
    """Represents a running upstream MCP server"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.tools: List[Dict[str, Any]] = []
        self.initialized = False
        self.server_id = f"{config.name}_{id(self)}"
    
    async def start(self):
        """Start the upstream server"""
        try:
            env = os.environ.copy()
            if self.config.env:
                env.update(self.config.env)
            
            logger.info(
                "Starting upstream server",
                server=self.config.name,
                command=self.config.command
            )
            
            self.process = subprocess.Popen(
                [self.config.command] + self.config.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=self.config.cwd,
                text=True,
                bufsize=1
            )
            
            # Wait a bit for server to start
            await asyncio.sleep(0.5)
            
            if self.process.poll() is not None:
                stderr = self.process.stderr.read() if self.process.stderr else ""
                raise RuntimeError(
                    f"Server {self.config.name} failed to start: {stderr}"
                )
            
            logger.info("Upstream server started", server=self.config.name)
            
        except Exception as e:
            logger.error(
                "Failed to start upstream server",
                server=self.config.name,
                error=str(e)
            )
            raise
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the server"""
        if not self.process:
            raise RuntimeError("Server not started")
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "safe-mcp-gateway",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self._send_request(init_request)
        self.initialized = True
        
        logger.info("Upstream server initialized", server=self.config.name)
        return response
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of tools from server"""
        if not self.initialized:
            await self.initialize()
        
        request = {
            "jsonrpc": "2.0",
            "id": f"tools-list-{self.server_id}",
            "method": "tools/list",
            "params": {}
        }
        
        response = await self._send_request(request)
        self.tools = response.get("result", {}).get("tools", [])
        
        logger.info(
            "Tools listed",
            server=self.config.name,
            count=len(self.tools)
        )
        
        return self.tools
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on this server"""
        request = {
            "jsonrpc": "2.0",
            "id": f"tool-call-{tool_name}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        return await self._send_request(request)
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request to server"""
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("Server not available")
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("No response from server")
            
            response = json.loads(response_line)
            
            if "error" in response:
                logger.error(
                    "Server returned error",
                    server=self.config.name,
                    error=response["error"]
                )
            
            return response
            
        except Exception as e:
            logger.error(
                "Failed to communicate with server",
                server=self.config.name,
                error=str(e)
            )
            raise
    
    async def stop(self):
        """Stop the server"""
        if self.process:
            logger.info("Stopping upstream server", server=self.config.name)
            self.process.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.create_subprocess_exec(self.process.pid),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                self.process.kill()
            
            self.process = None
            self.initialized = False


class UpstreamServerManager:
    """Manages multiple upstream MCP servers"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.servers: Dict[str, UpstreamServer] = {}
        self.server_configs: List[ServerConfig] = []
    
    def load_config(self, config_path: Optional[str] = None):
        """Load server configurations from file"""
        path = config_path or self.config_path
        if not path:
            raise ValueError("No config path specified")
        
        config_file = Path(path).expanduser()
        if not config_file.exists():
            logger.warning("Config file not found", path=str(config_file))
            return
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        servers = config_data.get("servers", [])
        for server_data in servers:
            config = ServerConfig(
                name=server_data["name"],
                command=server_data["command"],
                args=server_data.get("args", []),
                env=server_data.get("env"),
                cwd=server_data.get("cwd"),
                enabled=server_data.get("enabled", True)
            )
            self.server_configs.append(config)
        
        logger.info(
            "Loaded server configurations",
            path=str(config_file),
            count=len(self.server_configs)
        )
    
    async def start_all(self):
        """Start all configured servers"""
        for config in self.server_configs:
            if not config.enabled:
                logger.info("Server disabled, skipping", server=config.name)
                continue
            
            try:
                server = UpstreamServer(config)
                await server.start()
                await server.initialize()
                self.servers[server.server_id] = server
                
            except Exception as e:
                logger.error(
                    "Failed to start server",
                    server=config.name,
                    error=str(e)
                )
        
        logger.info("All servers started", count=len(self.servers))
    
    async def stop_all(self):
        """Stop all running servers"""
        for server_id, server in self.servers.items():
            try:
                await server.stop()
            except Exception as e:
                logger.error(
                    "Error stopping server",
                    server=server.config.name,
                    error=str(e)
                )
        
        self.servers.clear()
        logger.info("All servers stopped")
    
    def get_server(self, server_id: str) -> Optional[UpstreamServer]:
        """Get a server by ID"""
        return self.servers.get(server_id)
    
    def get_all_servers(self) -> List[UpstreamServer]:
        """Get list of all running servers"""
        return list(self.servers.values())
    
    async def discover_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Discover tools from all servers"""
        all_tools = {}
        
        for server_id, server in self.servers.items():
            try:
                tools = await server.list_tools()
                all_tools[server_id] = tools
            except Exception as e:
                logger.error(
                    "Failed to list tools",
                    server=server.config.name,
                    error=str(e)
                )
                all_tools[server_id] = []
        
        return all_tools

