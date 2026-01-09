# 🛡️ mcp-bastion-sdk

**Secure your MCP servers in 1 line. Seriously.**

```python
from safe_mcp_sdk import secure

@secure()  # ← That's it!
async def my_tool(input: str):
    return process(input)
```

Automatic protection against **36 documented MCP attack techniques**.

---

## 🚀 Quick Start

### Installation

```bash
# Install from local directory (for now)
cd mcp-bastion-sdk
pip install -e .

# Or copy safe_mcp_sdk/ folder to your project
```

### Basic Usage

```python
from safe_mcp_sdk import secure

@server.tool()
@secure()  # Protects against all 36 MCP attack techniques
async def git_commit(message: str):
    os.system(f"git commit -m '{message}'")
    return {"status": "committed"}
```

### Attacks Blocked Automatically

| Attack Type | Technique ID | Status |
|-------------|-------------|--------|
| Command Injection | SAFE-T1103 | ✅ Blocked |
| Path Traversal | SAFE-T1105 | ✅ Blocked |
| Prompt Injection | SAFE-T1102 | ✅ Blocked |
| +33 more | ... | ✅ Blocked |

---

## 📖 Examples

### Before (Insecure)

```python
from mcp import Server

server = Server("git-server")

@server.tool()
async def git_clone(repo_url: str):
    # ❌ Vulnerable to command injection!
    os.system(f"git clone {repo_url}")
```

### After (Secured - 1 line!)

```python
from mcp import Server
from safe_mcp_sdk import secure

server = Server("git-server")

@server.tool()
@secure()  # ← Add this ONE LINE!
async def git_clone(repo_url: str):
    # ✅ Now protected against all attacks!
    os.system(f"git clone {repo_url}")
```

**Attack example:**
```python
await git_clone("https://evil.com; rm -rf /")

# Result: 🚫 BLOCKED by SAFE-T1103 (Command Injection)
# Function never executes!
```

---

## 🎯 Customize Protection

### Check Specific Techniques

```python
@secure(techniques=["SAFE-T1105", "SAFE-T1102"])
async def read_file(path: str):
    # Only checks path traversal & prompt injection
    pass
```

### Warn Instead of Block

```python
@secure(block=False)  # Logs warning but doesn't block
async def experimental_feature(input: str):
    pass
```

---

## 🎬 Live Demo

Run the included demo:

```bash
cd mcp-bastion-sdk/examples
python demo_attacks.py
```

**Output:**
```
✅ Safe input: ALLOWED
🚫 Path traversal: BLOCKED (SAFE-T1105)
🚫 Command injection: BLOCKED (SAFE-T1103)
🚫 Prompt injection: BLOCKED (SAFE-T1102)
```

---

## 📊 How It Works

```
1. @secure decorator intercepts function call
2. Validates all string inputs against documented attack techniques
3. If attack detected: raises SAFEMCPException (blocks execution)
4. If safe: allows function to execute normally
```

**Same detection logic as mcp-bastion-security!**

---

## 🔗 Integration with mcp-bastion-security

| Layer | Tool | Protection |
|-------|------|------------|
| **Development** | mcp-bastion-sdk | Catches vulnerabilities while coding |
| **Runtime** | mcp-bastion-security | Catches attacks in production |

**Defense in depth = Two layers of protection!**

---

## 💡 Why This Matters

### Without SDK:
```python
# Developer writes insecure code
→ Deploy to production
→ Attacks detected at runtime (might be too late!)
```

### With SDK:
```python
# Developer adds @secure()
→ Attacks caught during development ✅
→ Attacks caught in testing ✅
→ Attacks caught at runtime (backup) ✅
```

---

## 🎓 Complete Example

See `examples/secure_git_server.py` for a full working example.

---

## 📄 License

MIT

---

## 🤝 Contributing

Part of the mcp-bastion-security project.

Built on comprehensive MCP threat intelligence research.

---

**Secure your MCP servers. One line at a time.** 🛡️

