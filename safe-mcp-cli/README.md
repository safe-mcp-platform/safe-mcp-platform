# mcp-bastion CLI

**Professional command-line interface for securing Model Context Protocol deployments**

[![PyPI version](https://img.shields.io/pypi/v/mcp-bastion.svg)](https://pypi.org/project/mcp-bastion/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-bastion.svg)](https://pypi.org/project/mcp-bastion/)
[![License](https://img.shields.io/pypi/l/mcp-bastion.svg)](https://github.com/mcp-bastion-security/mcp-bastion-security/blob/main/LICENSE)

---

## 🎯 What is mcp-bastion?

`mcp-bastion` is a zero-configuration CLI tool that transparently adds enterprise-grade security to your MCP deployments. It automatically discovers your MCP clients (Claude Desktop, Cursor, Windsurf, VS Code) and wraps them with 4-channel threat detection.

### Key Features

- ✅ **Auto-Discovery**: Finds all MCP clients on your system automatically
- ✅ **Transparent Protection**: No code changes required
- ✅ **4-Channel Detection**: Pattern + Rules + ML + Behavioral analysis
- ✅ **Reversible**: Clean install/uninstall
- ✅ **Multi-Client**: Works with Claude, Cursor, Windsurf, VS Code, Cline
- ✅ **Professional UI**: Beautiful terminal output with Rich

---

## 🚀 Quick Start

### Install (One-Time Setup)

```bash
# Install from PyPI
pip install mcp-bastion

# Or use uvx (no installation)
uvx mcp-bastion@latest scan
```

### Basic Usage (3 Steps)

```bash
# 1. Discover your MCP clients
mcp-bastion scan

# 2. Enable protection
mcp-bastion protect cursor

# 3. Check status
mcp-bastion status
```

**That's it!** Your Cursor IDE is now protected against:
- Prompt injection attacks
- Tool poisoning attacks
- Path traversal exploits
- Command injection
- SSRF attacks

---

## 📖 Commands

### `mcp-bastion scan`

Discover all MCP configurations on your system.

```bash
mcp-bastion scan                    # Quick scan
mcp-bastion scan --details          # Show server details
mcp-bastion scan --verbose          # Verbose output
```

**Example Output:**

```
🎯 Discovered MCP Configurations
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┓
┃ Client          ┃ Config Path                ┃ Servers ┃ Status  ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━┩
│ 💻 Cursor IDE   │ ~/.cursor/mcp.json         │ 3       │ ✅ Ready │
│ 🤖 Claude       │ ~/Library/.../Claude/...   │ 2       │ ✅ Ready │
│ 🏄 Windsurf     │ ~/.codeium/windsurf/...    │ 1       │ ✅ Ready │
└─────────────────┴────────────────────────────┴─────────┴─────────┘
```

---

### `mcp-bastion protect`

Enable runtime protection for MCP client(s).

```bash
mcp-bastion protect cursor          # Protect Cursor IDE
mcp-bastion protect claude          # Protect Claude Desktop
mcp-bastion protect --all           # Protect all clients
mcp-bastion protect --config ~/.custom/mcp.json  # Custom config
```

**What Happens:**
1. Creates backup of your config (`.mcp-bastion-backup`)
2. Wraps MCP servers with mcp-bastion-gateway
3. All MCP traffic now flows through 4-channel detection
4. Threats are automatically blocked

**Options:**

```bash
--gateway-url URL      # Gateway URL (default: http://localhost:8002)
--detection-url URL    # Detection API URL (default: http://localhost:8001)
--admin-url URL        # Admin dashboard URL (default: http://localhost:8000)
--no-logging           # Disable request logging
--no-blocking          # Log only (don't block threats)
--quiet                # Minimal output
```

---

### `mcp-bastion unprotect`

Disable runtime protection (restore original configs).

```bash
mcp-bastion unprotect cursor        # Unprotect Cursor IDE
mcp-bastion unprotect --all         # Unprotect all clients
mcp-bastion unprotect --config ~/.custom/mcp.json  # Custom config
```

**What Happens:**
1. Restores original config from backup
2. Removes mcp-bastion-gateway wrapper
3. MCP traffic flows directly (unprotected)

---

### `mcp-bastion status`

Show protection status for all MCP clients.

```bash
mcp-bastion status
```

**Example Output:**

```
📊 Protection Status

MCP Client Protection Status
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Client          ┃ Config Path                ┃ Status        ┃ Servers ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ 💻 Cursor IDE   │ ~/.cursor/mcp.json         │ 🛡️  Protected  │ 3       │
│ 🤖 Claude       │ ~/Library/.../Claude/...   │ ❌ Unprotected │ 2       │
└─────────────────┴────────────────────────────┴───────────────┴─────────┘

Summary: 1/2 clients protected
```

---

### `mcp-bastion logs`

View security logs (coming soon).

```bash
mcp-bastion logs                    # Recent logs
mcp-bastion logs --tail 100         # Last 100 logs
mcp-bastion logs --follow           # Real-time streaming
mcp-bastion logs --filter "blocked" # Filter by keyword
```

---

### `mcp-bastion dashboard`

Launch the admin dashboard in your browser.

```bash
mcp-bastion dashboard               # Open http://localhost:8000
mcp-bastion dashboard --url http://production:8000
```

---

## 🏗️ How It Works

### Before Protection

```
┌─────────┐         ┌───────────┐         ┌────────────────┐
│ Cursor  │────────▶│ MCP Server│────────▶│ Your Filesystem│
└─────────┘         └───────────┘         └────────────────┘
                                            ⚠️  No protection!
```

### After Protection

```
┌─────────┐    ┌──────────────────┐    ┌───────────┐    ┌────────────┐
│ Cursor  │───▶│ mcp-bastion-gateway │───▶│ MCP Server│───▶│ Filesystem │
└─────────┘    └──────────────────┘    └───────────┘    └────────────┘
                         │
                         │ 4-Channel Detection
                         ▼
               ┌──────────────────────┐
               │  Pattern Matching    │ 5-10ms
               │  Rule Engine         │ 8-12ms
               │  ML Model (BERT)     │ 15-20ms
               │  Behavioral Analysis │ 10-15ms
               └──────────────────────┘
                         │
                         ▼
                   ✅ Allow / 🚫 Block
```

**Total Latency:** 35-50ms (transparent to users)

---

## 🛡️ Security Features

### 4-Channel Threat Detection

| Channel | Technique | Latency | Threats Detected |
|---------|-----------|---------|------------------|
| **Pattern** | Regex + Signatures | 5-10ms | Known attack patterns, malicious payloads |
| **Rules** | Policy Engine | 8-12ms | Path traversal, privilege escalation |
| **ML** | BERT Classifier | 15-20ms | Novel prompt injections, obfuscation |
| **Behavioral** | Context Analysis | 10-15ms | Anomalous behavior, SSRF, data exfiltration |

**Confidence Aggregation:**
- Pattern (30%)
- Rules (35%)
- ML (25%)
- Behavioral (10%)

**Decision:** Block if confidence > 70%

---

## 🆚 Comparison with mcp-scan

| Feature | mcp-scan (Invariant) | mcp-bastion (This Tool) |
|---------|---------------------|---------------------|
| **Auto-Discovery** | ✅ | ✅ |
| **CLI Wrapper** | ✅ | ✅ |
| **Transparent Protection** | ✅ | ✅ |
| **Detection Channels** | 2 (Pattern + Basic ML) | **4 (Pattern + Rules + ML + Behavioral)** |
| **Admin Dashboard** | ❌ CLI only | ✅ React UI |
| **Database Audit Logs** | ❌ File-based | ✅ PostgreSQL |
| **Policy Engine** | ⚠️ Basic guardrails | ✅ Sophisticated rules |
| **Enterprise Features** | ⚠️ Limited | ✅ Full compliance |

**Result:** mcp-bastion = mcp-scan's ease of use + superior security

---

## 📦 Installation Options

### Option 1: PyPI (Recommended)

```bash
pip install mcp-bastion
```

### Option 2: uvx (No Installation)

```bash
# Run without installing
uvx mcp-bastion@latest scan
uvx mcp-bastion@latest protect cursor
```

### Option 3: From Source

```bash
git clone https://github.com/mcp-bastion-security/mcp-bastion-security.git
cd mcp-bastion-security/mcp-bastion-cli
pip install -e .
```

---

## 🔧 Prerequisites

### 1. Install the Gateway (One-Time)

```bash
# Pull Docker images
cd mcp-bastion-security
docker-compose pull

# Start services
docker-compose up -d

# Verify
curl http://localhost:8001/health  # Detection API
curl http://localhost:8000         # Admin Dashboard
```

### 2. Verify MCP Clients

Ensure you have at least one MCP client configured:
- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Cursor**: `~/.cursor/mcp.json`
- **Windsurf**: `~/.codeium/windsurf/mcp_config.json`

---

## 🎯 Use Cases

### 1. Developer Workstation Protection

```bash
# Protect your IDE
mcp-bastion protect cursor

# Continue coding normally
# All MCP calls are now automatically secured
```

### 2. Enterprise Deployment

```bash
# Protect all clients on employee machines
mcp-bastion protect --all

# Monitor via admin dashboard
mcp-bastion dashboard
```

### 3. CI/CD Pipeline

```bash
# In your CI script
mcp-bastion protect --config ./ci/mcp.json --no-blocking

# Run tests (logs threats without blocking)
pytest

# Review security logs
mcp-bastion logs --filter "blocked"
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

---

## 🔗 Links

- **Main Repository**: https://github.com/mcp-bastion-security/mcp-bastion-security
- **Documentation**: https://github.com/mcp-bastion-security/mcp-bastion-security#readme
- **Bug Reports**: https://github.com/mcp-bastion-security/mcp-bastion-security/issues
- **Demos**: https://github.com/mcp-bastion-security/demos-mcp-bastion-security

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/mcp-bastion-security/mcp-bastion-security/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mcp-bastion-security/mcp-bastion-security/discussions)

---

**Made with ❤️ by the MCP-Bastion Team**

