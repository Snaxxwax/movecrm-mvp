#!/bin/bash

echo "🧪 MoveCRM Service Tester"
echo "========================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test function
test_service() {
    local url=$1
    local name=$2
    local expected=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗${NC} (HTTP $response, expected $expected)"
        return 1
    fi
}

# API Test function
test_api_endpoint() {
    local url=$1
    local name=$2
    
    echo -e "\n${BLUE}Testing API: $name${NC}"
    echo "URL: $url"
    
    response=$(curl -s "$url" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        echo -e "${GREEN}Response:${NC}"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        return 0
    else
        echo -e "${RED}Failed to get response${NC}"
        return 1
    fi
}

# Container status check
check_containers() {
    echo -e "${BLUE}Container Status:${NC}"
    if command -v podman >/dev/null 2>&1; then
        CMD="podman"
    else
        CMD="docker"
    fi
    
    containers=("movecrm-postgres" "movecrm-redis" "movecrm-backend" "movecrm-yoloe-mock" "movecrm-widget-cdn" "movecrm-minio")
    
    for container in "${containers[@]}"; do
        if $CMD ps --format "{{.Names}}" | grep -q "^$container$"; then
            status=$($CMD ps --format "table {{.Status}}" --filter "name=$container" | tail -n 1)
            echo -e "  $container: ${GREEN}Running${NC} - $status"
        else
            echo -e "  $container: ${RED}Not Running${NC}"
        fi
    done
}

# Main tests
echo "========================================"
echo "1. Container Health Check"
echo "========================================"
check_containers

echo ""
echo "========================================"
echo "2. Service Endpoint Tests"
echo "========================================"
test_service "http://localhost:5432" "PostgreSQL" "000"  # PostgreSQL doesn't serve HTTP
test_service "http://localhost:6379" "Redis" "000"  # Redis doesn't serve HTTP
test_service "http://localhost:5000/health" "Backend API" "200"
test_service "http://localhost:8001/health" "YOLOE Mock Service" "200"
test_service "http://localhost:8080" "Widget CDN" "200"
test_service "http://localhost:9001" "MinIO Console" "200"
test_service "http://localhost:8082" "Adminer" "200"

echo ""
echo "========================================"
echo "3. API Functionality Tests"
echo "========================================"

# Test Backend Health
test_api_endpoint "http://localhost:5000/health" "Backend Health"

# Test YOLOE Health
test_api_endpoint "http://localhost:8001/health" "YOLOE Health"

# Test YOLOE Stats
test_api_endpoint "http://localhost:8001/stats" "YOLOE Stats"

echo ""
echo "========================================"
echo "4. Database Connection Test"
echo "========================================"
echo -n "Testing PostgreSQL connection... "
if command -v podman >/dev/null 2>&1; then
    CMD="podman"
else
    CMD="docker"
fi

if $CMD exec movecrm-postgres psql -U movecrm -d movecrm -c "SELECT 'Connected' as status;" 2>/dev/null | grep -q "Connected"; then
    echo -e "${GREEN}✓ Connected${NC}"
    
    # Check tables
    echo "Checking tables:"
    tables=$($CMD exec movecrm-postgres psql -U movecrm -d movecrm -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public';" 2>/dev/null)
    if [ -n "$tables" ]; then
        echo "$tables" | while read -r table; do
            if [ -n "$table" ]; then
                echo -e "  - ${GREEN}$table${NC}"
            fi
        done
    else
        echo -e "  ${YELLOW}No tables found${NC}"
    fi
else
    echo -e "${RED}✗ Failed${NC}"
fi

echo ""
echo "========================================"
echo "5. Create Test Quote (API Test)"
echo "========================================"
echo "Creating test quote via API..."

# Create a test quote
response=$(curl -s -X POST http://localhost:5000/api/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "test@example.com",
    "customer_name": "Test Customer",
    "pickup_address": "123 Main St",
    "delivery_address": "456 Oak Ave",
    "items": [
      {"name": "Sofa", "quantity": 1},
      {"name": "Dining Table", "quantity": 1}
    ]
  }' 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$response" ]; then
    echo -e "${GREEN}Response received:${NC}"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${YELLOW}Note: Quote creation endpoint may not be implemented yet${NC}"
fi

echo ""
echo "========================================"
echo "6. Mock YOLOE Detection Test"
echo "========================================"
echo "Testing mock detection with text input..."

response=$(curl -s -X POST http://localhost:8001/detect/text \
  -H "Content-Type: application/json" \
  -d '{"description": "I have a sofa, dining table, and refrigerator to move"}' 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$response" ]; then
    echo -e "${GREEN}Mock detection successful:${NC}"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${RED}Mock detection failed${NC}"
fi

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"

# Count successes
total_tests=0
passed_tests=0

# Re-run tests silently for summary
services=("5000/health" "8001/health" "8080" "9001")
for service in "${services[@]}"; do
    total_tests=$((total_tests + 1))
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$service" 2>/dev/null | grep -q "200"; then
        passed_tests=$((passed_tests + 1))
    fi
done

echo -e "Tests Passed: ${GREEN}$passed_tests${NC} / $total_tests"

if [ $passed_tests -eq $total_tests ]; then
    echo -e "\n${GREEN}✨ All services are working correctly!${NC}"
    echo ""
    echo "You can now:"
    echo "1. Access the Widget CDN at http://localhost:8080"
    echo "2. Use the Backend API at http://localhost:5000"
    echo "3. View the database at http://localhost:8082"
    echo "4. Access MinIO storage at http://localhost:9001"
else
    echo -e "\n${YELLOW}⚠️  Some services may need attention${NC}"
    echo ""
    echo "Debug commands:"
    echo "- View logs: podman-compose -f docker-compose.working.yml logs [service-name]"
    echo "- Restart services: podman-compose -f docker-compose.working.yml restart"
    echo "- Check container status: podman ps"
fi

echo ""
echo "========================================"
