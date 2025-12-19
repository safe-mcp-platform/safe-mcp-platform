#!/bin/bash

# SAFE-MCP-Platform Production Readiness Test
# This script validates the entire platform is ready for GitHub release

set -e

echo "🧪 SAFE-MCP-Platform Production Readiness Test"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

test_warn() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

# Test 1: Check essential files exist
echo "📋 Test 1: Essential Files"
echo "----------------------------"

files=("README.md" "INSTALL.md" "docker-compose.yml" "LICENSE" "CONTRIBUTING.md" ".gitignore")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        test_pass "$file exists"
    else
        test_fail "$file missing"
    fi
done
echo ""

# Test 2: Check backend structure
echo "🏗️  Test 2: Backend Structure"
echo "----------------------------"

backend_files=(
    "backend/config.py"
    "backend/requirements.txt"
    "backend/start_admin_service.py"
    "backend/services/admin_service.py"
    "backend/services/detection_service.py"
    "backend/database/models.py"
    "backend/database/connection.py"
)

for file in "${backend_files[@]}"; do
    if [ -f "$file" ]; then
        test_pass "$file exists"
    else
        test_fail "$file missing"
    fi
done
echo ""

# Test 3: Check techniques
echo "📚 Test 3: Techniques & Patterns"
echo "----------------------------"

technique_count=$(find backend/backend/safe_mcp_data/techniques -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
if [ "$technique_count" -ge 30 ]; then
    test_pass "Found $technique_count technique definitions (>= 30)"
else
    test_fail "Only $technique_count technique definitions found (expected >= 30)"
fi

# Check for T1102 and T1105 patterns
if [ -f "backend/patterns/safe-t1102-prompts.txt" ]; then
    pattern_count=$(wc -l < backend/patterns/safe-t1102-prompts.txt | tr -d ' ')
    test_pass "SAFE-T1102 patterns file exists ($pattern_count patterns)"
else
    test_fail "SAFE-T1102 patterns file missing"
fi

if [ -f "backend/patterns/safe-t1105-paths.txt" ]; then
    pattern_count=$(wc -l < backend/patterns/safe-t1105-paths.txt | tr -d ' ')
    test_pass "SAFE-T1105 patterns file exists ($pattern_count patterns)"
else
    test_fail "SAFE-T1105 patterns file missing"
fi
echo ""

# Test 4: Check SDK
echo "🛡️  Test 4: SAFE-MCP-SDK"
echo "----------------------------"

sdk_files=(
    "safe-mcp-sdk/safe_mcp_sdk/__init__.py"
    "safe-mcp-sdk/safe_mcp_sdk/decorators.py"
    "safe-mcp-sdk/safe_mcp_sdk/validators.py"
    "safe-mcp-sdk/safe_mcp_sdk/exceptions.py"
    "safe-mcp-sdk/examples/demo_attacks.py"
    "safe-mcp-sdk/setup.py"
    "safe-mcp-sdk/README.md"
)

for file in "${sdk_files[@]}"; do
    if [ -f "$file" ]; then
        test_pass "$file exists"
    else
        test_fail "$file missing"
    fi
done

# Test SDK imports
echo ""
echo "Testing SDK imports..."
cd safe-mcp-sdk
if python3 -c "from safe_mcp_sdk import secure, SAFEMCPException; print('Imports OK')" 2>/dev/null; then
    test_pass "SDK imports work"
else
    test_fail "SDK imports failed"
fi
cd ..
echo ""

# Test 5: Check frontend
echo "🎨 Test 5: Frontend"
echo "----------------------------"

if [ -f "frontend/package.json" ]; then
    test_pass "package.json exists"
else
    test_fail "package.json missing"
fi

if [ -f "frontend/vite.config.ts" ]; then
    test_pass "vite.config.ts exists"
    
    # Check if ports are correct
    if grep -q "localhost:8000" frontend/vite.config.ts; then
        test_pass "Admin port (8000) correctly configured in Vite"
    else
        test_fail "Admin port not correctly configured (should be 8000)"
    fi
    
    if grep -q "localhost:8001" frontend/vite.config.ts; then
        test_pass "Detection port (8001) correctly configured in Vite"
    else
        test_fail "Detection port not correctly configured (should be 8001)"
    fi
else
    test_fail "vite.config.ts missing"
fi
echo ""

# Test 6: Check configuration
echo "⚙️  Test 6: Configuration"
echo "----------------------------"

if grep -q "ADMIN_PORT.*8000" backend/config.py; then
    test_pass "Admin port default is 8000"
else
    test_warn "Admin port default might not be 8000"
fi

if grep -q "DETECTION_PORT.*8001" backend/config.py; then
    test_pass "Detection port default is 8001"
else
    test_warn "Detection port default might not be 8001"
fi

if grep -q "GATEWAY_PORT.*8002" backend/config.py; then
    test_pass "Gateway port default is 8002"
else
    test_warn "Gateway port default might not be 8002"
fi
echo ""

# Test 7: Check for hardcoded secrets
echo "🔐 Test 7: Security Check"
echo "----------------------------"

# Check .gitignore
if grep -q ".env" .gitignore; then
    test_pass ".env in .gitignore"
else
    test_fail ".env not in .gitignore"
fi

if grep -q "*.log" .gitignore; then
    test_pass "Log files in .gitignore"
else
    test_fail "Log files not in .gitignore"
fi

# Check for obvious secrets (very basic check)
if grep -r "sk-[a-zA-Z0-9]\{20,\}" --include="*.py" --include="*.ts" . 2>/dev/null | grep -v "node_modules" | grep -v "example" | grep -v "YOUR-KEY" > /dev/null; then
    test_fail "Possible real API keys found in code"
else
    test_pass "No obvious API keys in code"
fi
echo ""

# Test 8: Check Docker config
echo "🐳 Test 8: Docker Configuration"
echo "----------------------------"

if grep -q "version:" docker-compose.yml; then
    test_warn "docker-compose.yml has deprecated 'version' field"
else
    test_pass "docker-compose.yml has no deprecated 'version' field"
fi

if grep -q "safemcp-db" docker-compose.yml; then
    test_pass "Database service defined"
else
    test_fail "Database service not defined"
fi

if grep -q "safemcp-admin" docker-compose.yml; then
    test_pass "Admin service defined"
else
    test_fail "Admin service not defined"
fi

if grep -q "safemcp-detection" docker-compose.yml; then
    test_pass "Detection service defined"
else
    test_fail "Detection service not defined"
fi

if grep -q "safemcp-gateway" docker-compose.yml; then
    test_pass "Gateway service defined"
else
    test_fail "Gateway service not defined"
fi
echo ""

# Test 9: Check documentation consistency
echo "📖 Test 9: Documentation Consistency"
echo "----------------------------"

# Check README ports
if grep -q "localhost:8000" README.md; then
    test_pass "README mentions correct admin port (8000)"
else
    test_warn "README might not mention correct admin port"
fi

if grep -q "localhost:8001" README.md; then
    test_pass "README mentions correct detection port (8001)"
else
    test_warn "README might not mention correct detection port"
fi

# Check INSTALL ports
if grep -q "localhost:8000" INSTALL.md; then
    test_pass "INSTALL.md mentions correct admin port (8000)"
else
    test_warn "INSTALL.md might not mention correct admin port"
fi
echo ""

# Test 10: Check for temporary files
echo "🧹 Test 10: Cleanup Check"
echo "----------------------------"

temp_files=$(find . -name "*.tmp" -o -name "*.bak" -o -name "*.swp" 2>/dev/null | wc -l | tr -d ' ')
if [ "$temp_files" -eq 0 ]; then
    test_pass "No temporary files found"
else
    test_warn "Found $temp_files temporary files"
fi

# Check for too many emoji docs (should only have 2-3 key ones)
emoji_docs=$(find . -maxdepth 1 -name "*_*.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$emoji_docs" -le 5 ]; then
    test_pass "Reasonable number of status docs ($emoji_docs)"
else
    test_warn "Many status docs ($emoji_docs) - consider cleanup"
fi
echo ""

# Test 11: Python syntax check
echo "🐍 Test 11: Python Syntax"
echo "----------------------------"

python_errors=0
for file in $(find backend -name "*.py" 2>/dev/null | head -20); do
    if python3 -m py_compile "$file" 2>/dev/null; then
        :  # Silent success
    else
        test_fail "Syntax error in $file"
        python_errors=$((python_errors + 1))
    fi
done

if [ "$python_errors" -eq 0 ]; then
    test_pass "All checked Python files have valid syntax"
fi
echo ""

# Final Summary
echo "=============================================="
echo "📊 FINAL RESULTS"
echo "=============================================="
echo ""
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Platform is production-ready!${NC}"
    echo ""
    echo "✅ Ready to:"
    echo "  1. git add ."
    echo "  2. git commit -m 'feat: Initial release v1.0.0'"
    echo "  3. git push origin main"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please fix before release.${NC}"
    exit 1
fi

