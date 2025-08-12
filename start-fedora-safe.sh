#!/bin/bash

echo "🚀 MoveCRM Fedora-Safe Startup"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Clean up
echo "Cleaning up old containers..."
podman-compose -f docker-compose.working.yml down 2>/dev/null
podman rm -f $(podman ps -aq --filter name=movecrm) 2>/dev/null

# Step 2: Start PostgreSQL first
echo ""
echo "Starting PostgreSQL..."
podman-compose -f docker-compose.working.yml up -d postgres

# Step 3: Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to initialize..."
sleep 10

# Check if PostgreSQL is ready
for i in {1..30}; do
    if podman exec movecrm-postgres pg_isready -U movecrm -d movecrm >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Step 4: Load the database schema
echo ""
echo "Loading database schema..."
if [ -f "docs/database_schema_simple.sql" ]; then
    podman exec -i movecrm-postgres psql -U movecrm -d movecrm < docs/database_schema_simple.sql 2>/dev/null && \
    echo -e "${GREEN}✓ Database schema loaded${NC}" || \
    echo -e "${YELLOW}Schema may already be loaded${NC}"
else
    echo "Creating minimal schema..."
    podman exec movecrm-postgres psql -U movecrm -d movecrm -c "
    CREATE EXTENSION IF NOT EXISTS 'uuid-ossp';
    CREATE TABLE IF NOT EXISTS tenants (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name VARCHAR(255) NOT NULL,
        slug VARCHAR(50) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    INSERT INTO tenants (name, slug) VALUES ('Demo Company', 'demo') ON CONFLICT DO NOTHING;
    " && echo -e "${GREEN}✓ Minimal schema created${NC}"
fi

# Step 5: Start remaining services
echo ""
echo "Starting remaining services..."
podman-compose -f docker-compose.working.yml up -d redis minio backend yoloe-mock widget-cdn adminer

# Step 6: Wait for services
echo ""
echo "Waiting for all services to start (30 seconds)..."
sleep 30

# Step 7: Check status
echo ""
echo "========================================"
echo -e "${GREEN}Service Status:${NC}"
echo "========================================"
podman ps --format "table {{.Names}}\t{{.Status}}" | grep movecrm

# Step 8: Test services
echo ""
echo "========================================"
echo -e "${GREEN}Testing Services:${NC}"
echo "========================================"

test_service() {
    local url=$1
    local name=$2
    
    echo -n "$name: "
    if curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -q "200\|404"; then
        echo -e "${GREEN}✓ Working${NC}"
    else
        echo "⏳ Starting up..."
    fi
}

test_service "http://localhost:5000/health" "Backend API"
test_service "http://localhost:8001/health" "YOLOE Mock"
test_service "http://localhost:8080" "Widget CDN"
test_service "http://localhost:9001" "MinIO Console"

echo ""
echo "========================================"
echo -e "${GREEN}Access URLs:${NC}"
echo "========================================"
echo "Backend API:    http://localhost:5000"
echo "YOLOE Mock:     http://localhost:8001"
echo "Widget CDN:     http://localhost:8080"
echo "MinIO Console:  http://localhost:9001"
echo "Adminer:        http://localhost:8082"

echo ""
echo "If services are not responding, wait another 30 seconds"
echo "or check logs: podman-compose -f docker-compose.working.yml logs [service]"
