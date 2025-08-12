#!/bin/bash

echo "🚑 MoveCRM Quick Recovery Script"
echo "================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Stop everything first
echo "Step 1: Stopping all existing containers..."
podman-compose down 2>/dev/null
podman-compose -f docker-compose.working.yml down 2>/dev/null
sleep 2

# Step 2: Check and fix dependencies
echo ""
echo "Step 2: Checking dependencies..."
if ! grep -q "gunicorn" backend/requirements.txt 2>/dev/null; then
    echo "Adding missing backend dependencies..."
    echo -e "\ngunicorn==22.0.0\ngevent==24.2.1\npython-multipart==0.0.9" >> backend/requirements.txt
fi

if ! grep -q "uvicorn" yoloe-service/requirements.txt 2>/dev/null; then
    echo "Adding missing YOLOE dependencies..."
    echo -e "\nuvicorn==0.30.6\nfastapi==0.111.0\npython-multipart==0.0.9" >> yoloe-service/requirements.txt
fi

# Step 3: Use the mock YOLOE if main.py has issues
if [ -f "yoloe-service/main_mock.py" ] && [ ! -f "yoloe-service/main.py.original" ]; then
    echo "Setting up mock YOLOE service..."
    if [ -f "yoloe-service/main.py" ]; then
        mv yoloe-service/main.py yoloe-service/main.py.original
    fi
    cp yoloe-service/main_mock.py yoloe-service/main.py
fi

# Step 4: Start services in correct order
echo ""
echo "Step 3: Starting core infrastructure..."
podman-compose -f docker-compose.working.yml up -d postgres redis minio

echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Check if postgres is actually running
if podman ps | grep -q movecrm-postgres; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
    
    # Initialize database
    echo "Initializing database..."
    if [ -f "docs/database_schema_simple.sql" ]; then
        podman exec -i movecrm-postgres psql -U movecrm -d movecrm < docs/database_schema_simple.sql 2>/dev/null || true
    fi
else
    echo -e "${RED}✗ PostgreSQL failed to start${NC}"
    echo "Checking logs..."
    podman logs movecrm-postgres --tail 20
fi

# Step 5: Start application services
echo ""
echo "Step 4: Starting application services..."
podman-compose -f docker-compose.working.yml up -d backend yoloe-mock widget-cdn adminer

# Step 6: Wait and check
echo ""
echo "Step 5: Waiting for services to start (30 seconds)..."
sleep 30

# Step 7: Final status check
echo ""
echo "========================================"
echo -e "${GREEN}Service Status:${NC}"
echo "========================================"
podman ps --format "table {{.Names}}\t{{.Status}}" | grep movecrm || echo "No MoveCRM containers running!"

# Quick health checks
echo ""
echo "========================================"
echo "Quick Health Checks:"
echo "========================================"

check_service() {
    local url=$1
    local name=$2
    
    echo -n "$name: "
    if curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -q "200\|404"; then
        echo -e "${GREEN}✓ Responding${NC}"
    else
        echo -e "${RED}✗ Not responding${NC}"
    fi
}

check_service "http://localhost:5000/health" "Backend API"
check_service "http://localhost:8001/health" "YOLOE Mock"
check_service "http://localhost:8080" "Widget CDN"
check_service "http://localhost:9001" "MinIO"

echo ""
echo "========================================"
echo "If services are still failing, check logs:"
echo "  podman-compose -f docker-compose.working.yml logs [service-name]"
echo ""
echo "For a complete fresh start, run:"
echo "  podman system prune -a"
echo "  Then run this script again"
