#!/bin/bash

# Quick Test Script for MCP-Bastion-Security
# Run this before pushing to GitHub

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🧪 MCP-BASTION-SECURITY QUICK TEST              ║${NC}"
echo -e "${BLUE}║  Testing core functionality before push       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: SDK Demo
echo -e "${YELLOW}[1/5]${NC} Testing SDK (Most Critical)..."
cd mcp-bastion-sdk/examples
if python demo_attacks.py 2>&1 | grep -q "Attack BLOCKED"; then
    echo -e "${GREEN}✅ SDK Test PASSED${NC} - Attacks are blocked"
else
    echo -e "${RED}❌ SDK Test FAILED${NC}"
    exit 1
fi
cd ../..
echo ""

# Test 2: Docker Compose Syntax
echo -e "${YELLOW}[2/5]${NC} Checking Docker Compose..."
if docker-compose config > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Compose VALID${NC}"
else
    echo -e "${RED}❌ Docker Compose INVALID${NC}"
    exit 1
fi
echo ""

# Test 3: Python Syntax
echo -e "${YELLOW}[3/5]${NC} Checking Python syntax..."
python_errors=0
for file in backend/config.py backend/services/admin_service.py backend/services/detection_service.py; do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${RED}❌ Syntax error in $file${NC}"
        python_errors=$((python_errors + 1))
    fi
done

if [ "$python_errors" -eq 0 ]; then
    echo -e "${GREEN}✅ Python Syntax VALID${NC}"
else
    echo -e "${RED}❌ Found $python_errors Python syntax errors${NC}"
    exit 1
fi
echo ""

# Test 4: Documentation Check
echo -e "${YELLOW}[4/5]${NC} Checking essential files..."
missing_files=0
for file in README.md INSTALL.md CONTRIBUTING.md LICENSE docker-compose.yml; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Missing: $file${NC}"
        missing_files=$((missing_files + 1))
    fi
done

if [ "$missing_files" -eq 0 ]; then
    echo -e "${GREEN}✅ All Essential Files Present${NC}"
else
    echo -e "${RED}❌ Missing $missing_files essential files${NC}"
    exit 1
fi
echo ""

# Test 5: Technique Definitions
echo -e "${YELLOW}[5/5]${NC} Checking technique definitions..."
technique_count=$(find backend/backend/safe_mcp_data/techniques -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
if [ "$technique_count" -ge 30 ]; then
    echo -e "${GREEN}✅ Found $technique_count technique definitions${NC}"
else
    echo -e "${RED}❌ Only $technique_count techniques found (expected >= 30)${NC}"
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ✅ ALL QUICK TESTS PASSED!                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}🎉 Core functionality verified!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start services: ${YELLOW}docker-compose up -d${NC}"
echo "  2. Wait 30s, then test: ${YELLOW}curl http://localhost:8001/health${NC}"
echo "  3. Open dashboard: ${YELLOW}open http://localhost:8000${NC}"
echo "  4. Run full test: ${YELLOW}./test_production_ready.sh${NC}"
echo ""
echo "When satisfied → ${GREEN}PUSH TO GITHUB!${NC} 🚀"
echo ""

