"""
Tool Router
Routes tool calls to appropriate upstream MCP servers
"""

from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class ToolInfo:
    """Information about a registered tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_id: str
    server_name: str


class ToolRouter:
    """Routes MCP tool calls to upstream servers"""
    
    def __init__(self):
        # Map: tool_name -> ToolInfo
        self.tool_map: Dict[str, ToolInfo] = {}
        
        # Track tools per server
        self.server_tools: Dict[str, List[str]] = {}
        
        logger.info("Tool router initialized")
    
    def register_tools(
        self,
        server_id: str,
        server_name: str,
        tools: List[Dict[str, Any]]
    ):
        """Register tools from an upstream server"""
        registered_count = 0
        
        for tool in tools:
            tool_name = tool.get("name")
            if not tool_name:
                logger.warning("Tool missing name", server=server_name)
                continue
            
            # Handle name conflicts by prefixing with server name
            if tool_name in self.tool_map:
                original_server = self.tool_map[tool_name].server_name
                logger.warning(
                    "Tool name conflict detected",
                    tool=tool_name,
                    servers=[original_server, server_name]
                )
                # Prefix both tools with server name
                self._rename_conflicting_tool(tool_name, original_server)
                tool_name = f"{server_name}/{tool_name}"
            
            tool_info = ToolInfo(
                name=tool_name,
                description=tool.get("description", ""),
                input_schema=tool.get("inputSchema", {}),
                server_id=server_id,
                server_name=server_name
            )
            
            self.tool_map[tool_name] = tool_info
            
            if server_id not in self.server_tools:
                self.server_tools[server_id] = []
            self.server_tools[server_id].append(tool_name)
            
            registered_count += 1
        
        logger.info(
            "Tools registered",
            server=server_name,
            count=registered_count,
            total_tools=len(self.tool_map)
        )
    
    def _rename_conflicting_tool(self, tool_name: str, original_server: str):
        """Rename a tool that has a conflict"""
        if tool_name not in self.tool_map:
            return
        
        tool_info = self.tool_map[tool_name]
        new_name = f"{original_server}/{tool_name}"
        
        # Update tool map
        del self.tool_map[tool_name]
        tool_info.name = new_name
        self.tool_map[new_name] = tool_info
        
        # Update server tools list
        server_id = tool_info.server_id
        if server_id in self.server_tools:
            self.server_tools[server_id].remove(tool_name)
            self.server_tools[server_id].append(new_name)
        
        logger.info(
            "Tool renamed due to conflict",
            original=tool_name,
            new=new_name
        )
    
    def unregister_server(self, server_id: str):
        """Unregister all tools from a server"""
        if server_id not in self.server_tools:
            return
        
        tool_names = self.server_tools[server_id].copy()
        for tool_name in tool_names:
            if tool_name in self.tool_map:
                del self.tool_map[tool_name]
        
        del self.server_tools[server_id]
        
        logger.info(
            "Server tools unregistered",
            server=server_id,
            count=len(tool_names)
        )
    
    def get_tool_server(self, tool_name: str) -> Optional[str]:
        """Get server ID for a tool"""
        tool_info = self.tool_map.get(tool_name)
        if tool_info:
            return tool_info.server_id
        return None
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get list of all registered tools"""
        tools = []
        for tool_info in self.tool_map.values():
            tools.append({
                "name": tool_info.name,
                "description": tool_info.description,
                "inputSchema": tool_info.input_schema
            })
        return tools
    
    def get_server_tools(self, server_id: str) -> List[str]:
        """Get list of tools for a specific server"""
        return self.server_tools.get(server_id, [])
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """Get detailed info about a tool"""
        return self.tool_map.get(tool_name)
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered"""
        return tool_name in self.tool_map
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "total_tools": len(self.tool_map),
            "total_servers": len(self.server_tools),
            "servers": {
                server_id: len(tools)
                for server_id, tools in self.server_tools.items()
            }
        }

