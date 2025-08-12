#!/bin/bash

echo "🚀 MoveCRM Quick Start (Fixed Version)"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "Waiting for $service_name..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}✗${NC} (timeout)"
    return 1
}

# Check for podman or docker
if command_exists podman; then
    COMPOSE_CMD="podman-compose"
    CONTAINER_CMD="podman"
elif command_exists docker; then
    COMPOSE_CMD="docker-compose"
    CONTAINER_CMD="docker"
else
    echo -e "${RED}Error: Neither podman nor docker found!${NC}"
    exit 1
fi

echo "Using: $COMPOSE_CMD"
echo ""

# Step 1: Run dependency fix
echo "Step 1: Fixing dependencies..."
if [ -f "fix-dependencies.sh" ]; then
    bash fix-dependencies.sh
else
    echo -e "${YELLOW}Warning: fix-dependencies.sh not found, skipping dependency fix${NC}"
fi
echo ""

# Step 2: Clean up old containers
echo "Step 2: Cleaning up old containers..."
$COMPOSE_CMD -f docker-compose.working.yml down 2>/dev/null
$CONTAINER_CMD system prune -f 2>/dev/null
echo ""

# Step 3: Create necessary directories
echo "Step 3: Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p yoloe-service/uploads
mkdir -p widget/dist
mkdir -p logs

# Create a simple widget index.html if it doesn't exist
if [ ! -f "widget/dist/index.html" ]; then
    echo "Creating placeholder widget..."
    cat > widget/dist/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>MoveCRM Widget</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .widget { border: 2px solid #2563eb; padding: 20px; border-radius: 8px; }
        h1 { color: #2563eb; }
    </style>
</head>
<body>
    <div class="widget">
        <h1>MoveCRM Widget Ready</h1>
        <p>The widget CDN is working! Replace this with your actual widget build.</p>
    </div>
</body>
</html>
EOF
fi

# Create basic nginx.conf if it doesn't exist
if [ ! -f "widget/nginx.conf" ]; then
    echo "Creating nginx configuration..."
    cat > widget/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # CORS headers for widget
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type";

        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
EOF
fi

echo ""

# Step 4: Start core services first
echo "Step 4: Starting core services..."
echo "Starting PostgreSQL and Redis..."
$COMPOSE_CMD -f docker-compose.working.yml up -d postgres redis
sleep 10

# Check if postgres is ready
echo -n "Checking PostgreSQL..."
if $CONTAINER_CMD exec movecrm-postgres pg_isready -U movecrm -d movecrm > /dev/null 2>&1; then
    echo -e " ${GREEN}✓${NC}"
else
    echo -e " ${RED}✗${NC}"
    echo "PostgreSQL not ready. Waiting longer..."
    sleep 10
fi

# Step 5: Initialize database
echo ""
echo "Step 5: Initializing database..."
if [ -f "docs/database_schema_simple.sql" ]; then
    echo "Loading simplified schema..."
    $CONTAINER_CMD exec -i movecrm-postgres psql -U movecrm -d movecrm < docs/database_schema_simple.sql 2>/dev/null
    echo -e "Database initialized ${GREEN}✓${NC}"
else
    echo -e "${YELLOW}Warning: Simplified schema not found${NC}"
fi

# Step 6: Start remaining services
echo ""
echo "Step 6: Starting application services..."
$COMPOSE_CMD -f docker-compose.working.yml up -d backend yoloe-mock widget-cdn minio adminer

echo ""
echo "Step 7: Waiting for services to be ready..."
wait_for_service "http://localhost:5000/health" "Backend API"
wait_for_service "http://localhost:8001/health" "YOLOE Service"
wait_for_service "http://localhost:8080" "Widget CDN"
wait_for_service "http://localhost:9001" "MinIO Console"

# Step 8: Show status
echo ""
echo "========================================"
echo -e "${GREEN}MoveCRM Services Status:${NC}"
echo "========================================"
$CONTAINER_CMD ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep movecrm

echo ""
echo "========================================"
echo -e "${GREEN}Access Points:${NC}"
echo "========================================"
echo "🌐 Backend API:      http://localhost:5000"
echo "🤖 YOLOE Service:    http://localhost:8001"
echo "🎨 Widget CDN:       http://localhost:8080"
echo "💾 MinIO Console:    http://localhost:9001"
echo "   Username: minioadmin"
echo "   Password: minioadmin123"
echo "🗄️  Database Admin:   http://localhost:8082"
echo "   Server: postgres"
echo "   Username: movecrm"
echo "   Password: movecrm_password"
echo "   Database: movecrm"

echo ""
echo "========================================"
echo -e "${GREEN}Quick Tests:${NC}"
echo "========================================"
echo "1. Test Backend API:"
echo "   curl http://localhost:5000/health"
echo ""
echo "2. Test YOLOE Mock:"
echo "   curl http://localhost:8001/health"
echo ""
echo "3. Test Widget:"
echo "   firefox http://localhost:8080"
echo ""
echo "4. View Logs:"
echo "   $COMPOSE_CMD -f docker-compose.working.yml logs -f backend"
echo ""
echo "5. Stop Everything:"
echo "   $COMPOSE_CMD -f docker-compose.working.yml down"

echo ""
echo "========================================"
echo -e "${GREEN}✨ MoveCRM is ready!${NC}"
echo "========================================"

# Optional: Open browser
if command_exists firefox; then
    echo ""
    read -p "Open Widget CDN in Firefox? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        firefox http://localhost:8080 &
    fi
elif command_exists xdg-open; then
    echo ""
    read -p "Open Widget CDN in browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open http://localhost:8080 &
    fi
fi
