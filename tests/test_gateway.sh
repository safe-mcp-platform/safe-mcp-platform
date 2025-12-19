#!/bin/bash
# SAFE-MCP Gateway Integration Test

set -e

echo "🧪 SAFE-MCP Gateway Integration Test"
echo "====================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "$expected" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (got $http_code, expected $expected)"
        echo "Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if services are running
echo "1. Checking if services are running..."
if ! docker-compose ps | grep -q "safemcp-gateway.*Up"; then
    echo -e "${RED}✗ Gateway service not running!${NC}"
    echo "Run: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Gateway service is running${NC}"
echo ""

# Test health endpoint
echo "2. Testing health endpoint..."
test_endpoint "Gateway health" "http://localhost:5002/health" "200"
echo ""

# Test MCP initialize
echo "3. Testing MCP initialize..."
init_request='{"jsonrpc":"2.0","id":"test-1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0"}}}'

response=$(curl -s -X POST http://localhost:5002/mcp \
    -H "Content-Type: application/json" \
    -d "$init_request")

if echo "$response" | grep -q '"protocolVersion"'; then
    echo -e "${GREEN}✓ PASSED${NC} - Initialize successful"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} - Initialize failed"
    echo "Response: $response"
    ((TESTS_FAILED++))
fi
echo ""

# Test tools/list
echo "4. Testing tools/list..."
tools_request='{"jsonrpc":"2.0","id":"test-2","method":"tools/list","params":{}}'

response=$(curl -s -X POST http://localhost:5002/mcp \
    -H "Content-Type: application/json" \
    -d "$tools_request")

if echo "$response" | grep -q '"tools"'; then
    echo -e "${GREEN}✓ PASSED${NC} - Tools list returned"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} - Tools list failed"
    echo "Response: $response"
    ((TESTS_FAILED++))
fi
echo ""

# Test detection service integration
echo "5. Testing detection service integration..."
test_endpoint "Detection health" "http://localhost:5001/health" "200"
echo ""

# Summary
echo "====================================="
echo "Test Summary:"
echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
echo "====================================="

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi

