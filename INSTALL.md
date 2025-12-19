# Installation Guide

## Quick Start

Get SAFE-MCP-Platform running in 5 minutes.

### Prerequisites

- Docker 20.10+ & Docker Compose 2.0+
- One of: Claude Desktop, Cursor IDE, or VS Code with MCP
- 4GB RAM minimum, 8GB recommended

### Installation

```bash
git clone https://github.com/safe-mcp-platform/safe-mcp-platform
cd safe-mcp-platform
cp .env.example .env
docker-compose up -d
```

**Verify installation:**
```bash
docker-compose ps  # All services should show "Up"
curl http://localhost:8000/health  # Should return 200 OK
```

**Access dashboard:** http://localhost:8000 (default: admin@safemcp.com / admin123)

---

## Deployment Options

### Docker (Development)

```bash
docker-compose up -d
```

**Ports**: Admin (8000), Detection (8001), Gateway (8002), PostgreSQL (5432)

### Kubernetes (Production)

```bash
helm repo add safe-mcp https://charts.safe-mcp.org
helm install safe-mcp safe-mcp/safe-mcp-platform \
  --namespace safe-mcp \
  --set gateway.replicas=3 \
  --set detection.replicas=5
```

### Cloud Providers

<details>
<summary><b>AWS (ECS + RDS)</b></summary>

```bash
aws ecs create-cluster --cluster-name safe-mcp-cluster
# See deployment/aws/ for complete Terraform templates
```

</details>

<details>
<summary><b>GCP (Cloud Run + Cloud SQL)</b></summary>

```bash
gcloud run deploy safe-mcp-admin \
  --image gcr.io/<PROJECT>/safe-mcp-admin:latest \
  --platform managed \
  --region us-central1
```

</details>

<details>
<summary><b>Azure (Container Instances + PostgreSQL)</b></summary>

```bash
az container create \
  --resource-group safe-mcp \
  --name safe-mcp-platform \
  --image safemcp/platform:latest
```

</details>


---

## Configuration

### Environment Variables (.env)

```bash
# Core
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=<CHANGE_ME>
JWT_SECRET_KEY=<openssl rand -hex 32>

# Performance
DETECTION_WORKERS=32
CONFIDENCE_THRESHOLD=0.70

# Optional
HUGGINGFACE_TOKEN=<YOUR_TOKEN>
ENABLE_AUDIT_LOG=true
```

Full configuration reference: [docs/configuration.md](https://github.com/safe-mcp-platform/safe-mcp-platform/blob/main/docs/configuration.md)

---

## 🖥️ Client Integration

### Claude Desktop

**File**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

#### Method 1: Gateway Mode (Recommended)

```json
{
  "mcpServers": {
    "safe-gateway": {
      "command": "python",
      "args": ["-m", "safe_mcp.gateway_client"],
      "env": {
        "SAFE_MCP_GATEWAY": "http://localhost:8002",
        "SAFE_MCP_API_KEY": "sk-safe-mcp-YOUR-KEY-HERE"
      }
    },
    
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/you/Documents"],
      "protected": true,
      "via": "safe-gateway"
    },
    
    "database": {
      "command": "python",
      "args": ["-m", "mcp_server_sqlite", "/data/app.db"],
      "protected": true,
      "via": "safe-gateway"
    }
  }
}
```

#### Method 2: Per-Server SDK (Advanced)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "safe-mcp-wrap",
      "args": [
        "npx", "-y", "@modelcontextprotocol/server-filesystem", "/Users/you/Documents"
      ],
      "env": {
        "SAFE_MCP_API_KEY": "sk-safe-mcp-YOUR-KEY-HERE"
      }
    }
  }
}
```

**Install wrapper:**
```bash
pip install safe-mcp-client
```

---

### Cursor / VS Code

**File**: `.vscode/settings.json` or Cursor settings

```json
{
  "mcp.servers": {
    "safe-gateway": {
      "command": "safe-mcp-gateway",
      "args": ["--config", "./mcp-servers.json"],
      "env": {
        "SAFE_MCP_API_KEY": "sk-safe-mcp-YOUR-KEY-HERE",
        "SAFE_MCP_GATEWAY": "http://localhost:5002"
      }
    }
  }
}
```

**File**: `./mcp-servers.json`

```json
{
  "servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./"]
    },
    {
      "name": "git",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git", "--repository", "."]
    }
  ]
}
```

---

### Custom MCP Server Integration

**For developers building MCP servers:**

```python
# Original server
from mcp import Server

app = Server("my-server")

@app.tool()
def dangerous_operation(path: str):
    return execute_something(path)

if __name__ == "__main__":
    app.run()
```

```python
# Protected server
from mcp import Server
from safe_mcp import SafeMCPWrapper

app = Server("my-server")

@app.tool()
def dangerous_operation(path: str):
    return execute_something(path)

if __name__ == "__main__":
    # Wrap with SAFE-MCP protection
    protected = SafeMCPWrapper(
        app,
        api_key="sk-safe-mcp-YOUR-KEY",
        gateway_url="http://localhost:8001",  # Detection API
        techniques=["SAFE-T1102", "SAFE-T1105"]  # Check specific techniques
    )
    protected.run()
```

---

## 🏢 Enterprise Setup

### Multi-Tenant Configuration

**1. Create Tenants:**

```bash
# Using API
curl -X POST http://localhost:5000/api/v1/tenants \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Engineering Team",
    "quota": 100000,
    "allowed_techniques": ["SAFE-T1102", "SAFE-T1105"]
  }'

# Response includes tenant_id and API key
```

**2. Distribute API Keys:**

Each team gets their own API key:
- `sk-safe-mcp-team-engineering-xxx`
- `sk-safe-mcp-team-product-xxx`
- `sk-safe-mcp-team-research-xxx`

**3. Configure per Team:**

```json
// Engineering team config
{
  "mcpServers": {
    "safe-gateway": {
      "env": {
        "SAFE_MCP_API_KEY": "sk-safe-mcp-team-engineering-xxx",
        "SAFE_MCP_GATEWAY": "http://localhost:8002"
      }
    }
  }
}
```

---

### SSO Integration (Coming Soon)

```yaml
# config/sso.yml
sso:
  provider: okta  # or azure-ad, google-workspace
  client_id: <CLIENT_ID>
  client_secret: <CLIENT_SECRET>
  redirect_uri: https://safe-mcp.company.com/auth/callback
  
  # Auto-provision tenants
  auto_provision: true
  default_quota: 10000
  
  # Map SSO groups to tenants
  group_mapping:
    "Engineering": "team-engineering"
    "Product": "team-product"
```

---

### Compliance & Audit

**Enable audit logging:**

```bash
# .env
ENABLE_AUDIT_LOG=true
AUDIT_LOG_DESTINATION=postgresql  # or s3, elasticsearch
AUDIT_RETENTION_DAYS=365  # 1 year for compliance
```

**Export audit logs:**

```bash
# Export to CSV
curl -X GET "http://localhost:5000/api/v1/audit/export?format=csv&start=2024-01-01&end=2024-12-31" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -o audit-2024.csv

# Export to SIEM (Splunk, Datadog)
curl -X POST http://localhost:5000/api/v1/audit/export \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "splunk",
    "endpoint": "https://splunk.company.com:8088",
    "token": "<SPLUNK_HEC_TOKEN>"
  }'
```

---

## 🔧 Troubleshooting

### Issue 1: Services Won't Start

**Symptom:**
```
ERROR: Connection to database failed
```

**Solution:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart services
docker-compose down && docker-compose up -d
```

---

### Issue 2: Detection API Returns 500

**Symptom:**
```json
{"error": "Internal Server Error"}
```

**Solution:**
```bash
# Check detection service logs
docker-compose logs detection

# Common causes:
# 1. Missing ML models
export HUGGINGFACE_TOKEN=<YOUR_TOKEN>
docker-compose restart detection

# 2. Out of memory
# Increase Docker memory limit to 4GB+

# 3. Database connection timeout
# Check POSTGRES_HOST in .env
```

---

### Issue 3: High Latency (>200ms)

**Symptom:**
MCP calls take too long

**Solution:**
```bash
# 1. Increase detection workers
# Edit .env:
DETECTION_WORKERS=64  # Was 32

# 2. Enable caching
ENABLE_REDIS_CACHE=true
REDIS_URL=redis://localhost:6379

# 3. Disable ML for low-risk patterns
# Edit backend/config.py:
TECHNIQUE_CONFIGS["SAFE-T1102"]["use_ml"] = False  # Use patterns only

# Restart
docker-compose restart
```

---

### Issue 4: Claude Desktop Can't Connect

**Symptom:**
"MCP server 'safe-gateway' failed to start"

**Solution:**
```bash
# 1. Verify gateway is running
curl http://localhost:8002/health

# 2. Check Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp.log

# 3. Verify config syntax
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .

# 4. Test with minimal config
{
  "mcpServers": {
    "test": {
      "command": "echo",
      "args": ["test"]
    }
  }
}

# 5. Restart Claude Desktop completely
pkill Claude && open -a Claude
```

---

### Issue 5: False Positives

**Symptom:**
Legitimate MCP calls are blocked

**Solution:**
```bash
# 1. Check detection logs
curl "http://localhost:5000/api/v1/detections?status=blocked&limit=100" \
  -H "Authorization: Bearer <API_KEY>"

# 2. Adjust confidence threshold
# Edit .env:
CONFIDENCE_THRESHOLD=0.85  # Was 0.70 (higher = fewer blocks)

# 3. Disable specific techniques
curl -X PATCH "http://localhost:5000/api/v1/config/techniques/SAFE-T1105" \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{"enabled": false}'

# 4. Add whitelist patterns
curl -X POST "http://localhost:5000/api/v1/config/whitelist" \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{
    "pattern": "^/Users/alice/safe-dir/.*",
    "technique": "SAFE-T1105",
    "reason": "Trusted directory"
  }'
```

---

## 📊 Monitoring & Metrics

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health  # Admin
curl http://localhost:8001/health  # Detection
curl http://localhost:8002/health  # Gateway
```

### Prometheus Metrics

```bash
# Enable metrics endpoint
# .env
ENABLE_METRICS=true
METRICS_PORT=9090

# Scrape endpoint
curl http://localhost:9090/metrics
```

**Key metrics:**
- `safe_mcp_detections_total{technique="SAFE-T1102", action="blocked"}`
- `safe_mcp_detection_latency_seconds{quantile="0.95"}`
- `safe_mcp_gateway_requests_total{status="200"}`

### Grafana Dashboard

```bash
# Import dashboard
curl http://localhost:5000/api/v1/monitoring/grafana-dashboard.json

# Open Grafana
open http://localhost:3000
```

---

## 🆘 Support

- **Documentation**: https://docs.safe-mcp.org
- **GitHub Issues**: https://github.com/safe-mcp-platform/safe-mcp-platform/issues
- **Community Slack**: https://safe-mcp.slack.com
- **Email**: support@safe-mcp.org

---

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] All services show "Up" in `docker-compose ps`
- [ ] Dashboard accessible at http://localhost:8000
- [ ] Detection API responds: `curl http://localhost:8001/health`
- [ ] Gateway responds: `curl http://localhost:8002/health`
- [ ] API key generated and saved
- [ ] Claude Desktop config updated
- [ ] First MCP call successfully protected
- [ ] Detection logged in dashboard
- [ ] No errors in `docker-compose logs`

**All checked?** You're production-ready! 🚀

---

## 📚 Next Steps

1. Read [HOW_MCP_REALLY_WORKS.md](./HOW_MCP_REALLY_WORKS.md) for architecture deep dive
2. Review [CONTRIBUTING.md](./CONTRIBUTING.md) to add detection techniques
3. Check [ROADMAP.md](./ROADMAP.md) for upcoming features
4. Join our community to stay updated

**Happy MCP securing!** 🛡️

