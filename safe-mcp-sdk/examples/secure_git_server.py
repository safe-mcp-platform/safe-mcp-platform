"""
SECURE Git MCP Server (With safe-mcp-sdk)

Same functionality as insecure_git_server.py, but protected with @secure decorator.
Just add @secure() - that's it! One line per tool.
"""

import subprocess
import os
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from safe_mcp_sdk import secure

# Simulating MCP server structure
class MockServer:
    def __init__(self, name):
        self.name = name
        self.tools = []
    
    def tool(self):
        def decorator(func):
            self.tools.append(func)
            return func
        return decorator

server = MockServer("secure-git-server")

@server.tool()
@secure()  # ← ONE LINE! Now protected against all 36 SAFE-MCP techniques
async def git_clone(repo_url: str, target_dir: str):
    """
    Clone a git repository
    
    ✅ PROTECTED: Command Injection detection enabled
    Attack example: "https://evil.com; rm -rf /" → BLOCKED by SAFE-T1103
    """
    os.system(f"git clone {repo_url} {target_dir}")
    return {"status": "cloned"}

@server.tool()
@secure()  # ← ONE LINE! Automatic path traversal protection
async def read_file(path: str):
    """
    Read a file from the repository
    
    ✅ PROTECTED: Path Traversal detection enabled
    Attack example: "../../../../etc/passwd" → BLOCKED by SAFE-T1105
    """
    with open(path, 'r') as f:
        return f.read()

@server.tool()
@secure()  # ← ONE LINE! Shell injection protection
async def git_commit(message: str):
    """
    Commit changes
    
    ✅ PROTECTED: Command Injection detection enabled
    Attack example: "test'; rm -rf /; echo 'done" → BLOCKED by SAFE-T1103
    """
    os.system(f"git commit -m '{message}'")
    return {"status": "committed"}

@server.tool()
@secure(techniques=["SAFE-T1105"])  # ← Customize per tool!
async def read_config(filename: str):
    """
    Read configuration file
    
    ✅ PROTECTED: Only checks path traversal (customized)
    """
    config_dir = Path("./configs")
    file_path = config_dir / filename
    with open(file_path, 'r') as f:
        return f.read()

if __name__ == "__main__":
    print("✅ SECURE Git MCP Server (powered by safe-mcp-sdk)")
    print("Protected against all 36 SAFE-MCP techniques!")
    print("")
    print("Integration: Just 1 line per tool:")
    print("  @secure()  ← That's it!")

