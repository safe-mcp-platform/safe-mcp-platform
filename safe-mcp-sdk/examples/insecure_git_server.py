"""
INSECURE Git MCP Server (Before safe-mcp-sdk)

This demonstrates common vulnerabilities in MCP servers.
DO NOT USE THIS IN PRODUCTION!
"""

import subprocess
import os

# Simulating MCP server structure (would normally import from mcp package)
class MockServer:
    def __init__(self, name):
        self.name = name
        self.tools = []
    
    def tool(self):
        def decorator(func):
            self.tools.append(func)
            return func
        return decorator

server = MockServer("insecure-git-server")

@server.tool()
async def git_clone(repo_url: str, target_dir: str):
    """
    Clone a git repository
    
    ❌ VULNERABILITY: Command Injection
    An attacker could pass: repo_url="https://evil.com; rm -rf /"
    """
    # DANGEROUS: Direct shell execution without validation!
    os.system(f"git clone {repo_url} {target_dir}")
    return {"status": "cloned"}

@server.tool()
async def read_file(path: str):
    """
    Read a file from the repository
    
    ❌ VULNERABILITY: Path Traversal
    An attacker could pass: path="../../../../etc/passwd"
    """
    # DANGEROUS: No path validation!
    with open(path, 'r') as f:
        return f.read()

@server.tool()
async def git_commit(message: str):
    """
    Commit changes
    
    ❌ VULNERABILITY: Command Injection
    An attacker could pass: message="test'; rm -rf /; echo 'done"
    """
    # DANGEROUS: Shell injection via message!
    os.system(f"git commit -m '{message}'")
    return {"status": "committed"}

if __name__ == "__main__":
    print("⚠️  INSECURE Git MCP Server")
    print("This server has NO security protections!")
    print("Vulnerable to:")
    print("  - Command Injection (SAFE-T1103)")
    print("  - Path Traversal (SAFE-T1105)")
    print("  - Prompt Injection (SAFE-T1102)")

