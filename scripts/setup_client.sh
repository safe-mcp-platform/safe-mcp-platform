#!/bin/bash
# MCP-Bastion Platform Client Setup Script
# Configures Claude Desktop to use MCP-Bastion Gateway

set -e

echo "🛡️  MCP-Bastion - Client Setup"
echo "======================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
    OS="macOS"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    CLAUDE_CONFIG_DIR="$APPDATA/Claude"
    OS="Windows"
else
    CLAUDE_CONFIG_DIR="$HOME/.config/claude"
    OS="Linux"
fi

echo "Detected OS: $OS"
echo "Claude config directory: $CLAUDE_CONFIG_DIR"
echo ""

# Create mcp-bastion directory
MCP_BASTION_DIR="$HOME/.mcp-bastion"
mkdir -p "$SAFE_MCP_DIR"
echo "✓ Created $SAFE_MCP_DIR"

# Copy upstream servers template
if [ ! -f "$SAFE_MCP_DIR/servers.json" ]; then
    cp config-templates/upstream-servers.json "$SAFE_MCP_DIR/servers.json"
    echo "✓ Created upstream servers config"
else
    echo "⚠ Upstream servers config already exists, skipping"
fi

# Prompt for API key
echo ""
echo "Enter your MCP-Bastion API key:"
echo "(Get it from: http://localhost:5000/platform/account)"
read -p "API Key: " API_KEY

if [ -z "$API_KEY" ]; then
    echo "❌ API key required!"
    exit 1
fi

# Create Claude config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Check if config exists
CLAUDE_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
if [ -f "$CLAUDE_CONFIG" ]; then
    echo ""
    echo "⚠ Claude Desktop config already exists!"
    echo "File: $CLAUDE_CONFIG"
    echo ""
    read -p "Backup and replace? (y/n): " BACKUP
    
    if [ "$BACKUP" = "y" ]; then
        cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✓ Backed up existing config"
    else
        echo "❌ Installation cancelled"
        exit 1
    fi
fi

# Create new config
cat > "$CLAUDE_CONFIG" << EOF
{
  "mcpServers": {
    "mcp-bastion-gateway": {
      "command": "python",
      "args": ["-m", "safe_mcp.gateway_client"],
      "env": {
        "SAFE_MCP_GATEWAY_URL": "http://localhost:5002",
        "SAFE_MCP_API_KEY": "$API_KEY",
        "UPSTREAM_CONFIG": "$SAFE_MCP_DIR/servers.json"
      }
    }
  }
}
EOF

echo "✓ Created Claude Desktop config"
echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit $SAFE_MCP_DIR/servers.json to configure your MCP servers"
echo "2. Restart Claude Desktop"
echo "3. All MCP traffic will now be protected by MCP-Bastion!"
echo ""
echo "Dashboard: http://localhost:5000"
echo "View logs: http://localhost:5000/platform/results"
echo ""

