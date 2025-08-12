#!/bin/bash

echo "🔧 MoveCRM Troubleshooting Helper"
echo "================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect container runtime
if command -v podman >/dev/null 2>&1; then
    COMPOSE_CMD="podman-compose"
    CONTAINER_CMD="podman"
else
    COMPOSE_CMD="docker-compose"
    CONTAINER_CMD="docker"
fi

echo "Using: $CONTAINER_CMD"
echo ""

# Function to check and fix common issues
fix_issue() {
    local issue=$1
    echo -e "${YELLOW}Fixing: $issue${NC}"
}

# 1. Check container runtime
echo -e "${BLUE}1. Container Runtime Check${NC}"
echo "----------------------------"
if ! command -v $CONTAINER_CMD >/dev/null 2>&1; then
    echo -e "${RED}✗ $CONTAINER_CMD not found!${NC}"
    echo "  Install podman or docker first"
    exit 1
else
    echo -e "${GREEN}✓ $CONTAINER_CMD found${NC}"
    $CONTAINER_CMD --version
fi

if ! command -v $COMPOSE_CMD >/dev/null 2>&1; then
    echo -e "${RED}✗ $COMPOSE_CMD not found!${NC}"
    echo "  Install podman-compose or docker-compose"
    echo "  pip install podman-compose"
else
    echo -e "${GREEN}✓ $COMPOSE_CMD found${NC}"
fi

# 2. Check and fix permissions
echo ""
echo -e "${BLUE}2. File Permissions Check${NC}"
echo "----------------------------"

# Make scripts executable
scripts=("fix-dependencies.sh" "start-fixed.sh" "test-services.sh" "troubleshoot.sh")
for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        echo -e "${GREEN}✓${NC} $script is executable"
    fi
done

# Check database schema permissions
if [ -f "docs/database_schema.sql" ]; then
    chmod 644 docs/database_schema.sql
    echo -e "${GREEN}✓${NC} Database schema permissions fixed"
fi

if [ -f "docs/database_schema_simple.sql" ]; then
    chmod 644 docs/database_schema_simple.sql
    echo -e "${GREEN}✓${NC} Simple schema permissions fixed"
fi

# 3. Check running containers
echo ""
echo -e "${BLUE}3. Container Status${NC}"
echo "----------------------------"
running_containers=$($CONTAINER_CMD ps --format "{{.Names}}" | grep movecrm | wc -l)
echo "Running MoveCRM containers: $running_containers"

if [ $running_containers -gt 0 ]; then
    $CONTAINER_CMD ps --format "table {{.Names}}\t{{.Status}}\t{{.State}}" | grep movecrm
fi

# 4. Check for port conflicts
echo ""
echo -e "${BLUE}4. Port Availability Check${NC}"
echo "----------------------------"
ports=("5432:PostgreSQL" "6379:Redis" "5000:Backend" "8001:YOLOE" "8080:Widget" "9000:MinIO" "9001:MinIO-Console" "8082:Adminer")

for port_info in "${ports[@]}"; do
    port="${port_info%%:*}"
    service="${port_info#*:}"
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}✗${NC} Port $port ($service) is in use"
        
        # Check if it's our container
        if $CONTAINER_CMD ps --format "{{.Ports}}" | grep -q "$port"; then
            echo "  Used by MoveCRM container"
        else
            echo "  Used by another process - this may cause conflicts"
            echo "  Fix: Stop the other service or change the port in docker-compose.working.yml"
        fi
    else
        echo -e "${GREEN}✓${NC} Port $port ($service) is available"
    fi
done

# 5. Check container logs for errors
echo ""
echo -e "${BLUE}5. Recent Container Errors${NC}"
echo "----------------------------"

containers=("movecrm-postgres" "movecrm-backend" "movecrm-yoloe-mock" "movecrm-redis")
for container in "${containers[@]}"; do
    if $CONTAINER_CMD ps -a --format "{{.Names}}" | grep -q "^$container$"; then
        echo -e "\n${YELLOW}$container logs (last 5 lines):${NC}"
        $CONTAINER_CMD logs --tail 5 $container 2>&1 | grep -i -E "error|failed|exception|fatal" || echo "  No errors found"
    fi
done

# 6. Database connectivity check
echo ""
echo -e "${BLUE}6. Database Connectivity${NC}"
echo "----------------------------"
if $CONTAINER_CMD ps --format "{{.Names}}" | grep -q "movecrm-postgres"; then
    echo -n "Testing PostgreSQL connection... "
    if $CONTAINER_CMD exec movecrm-postgres pg_isready -U movecrm -d movecrm >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Connected${NC}"
        
        # Check if tables exist
        table_count=$($CONTAINER_CMD exec movecrm-postgres psql -U movecrm -d movecrm -t -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';" 2>/dev/null | tr -d ' ')
        echo "  Tables in database: $table_count"
        
        if [ "$table_count" = "0" ] || [ -z "$table_count" ]; then
            echo -e "  ${YELLOW}No tables found - database may need initialization${NC}"
            echo "  Fix: Run this command:"
            echo "    $CONTAINER_CMD exec -i movecrm-postgres psql -U movecrm -d movecrm < docs/database_schema_simple.sql"
        fi
    else
        echo -e "${RED}✗ Connection failed${NC}"
        echo "  PostgreSQL may still be starting or has errors"
    fi
else
    echo -e "${RED}PostgreSQL container not running${NC}"
fi

# 7. Common fixes
echo ""
echo -e "${BLUE}7. Common Fixes${NC}"
echo "----------------------------"

echo -e "${YELLOW}Issue: Containers won't start${NC}"
echo "  Fix: $COMPOSE_CMD -f docker-compose.working.yml down"
echo "       $CONTAINER_CMD system prune -f"
echo "       ./start-fixed.sh"
echo ""

echo -e "${YELLOW}Issue: Database errors${NC}"
echo "  Fix: $CONTAINER_CMD exec -i movecrm-postgres psql -U movecrm -d movecrm < docs/database_schema_simple.sql"
echo ""

echo -e "${YELLOW}Issue: Backend not responding${NC}"
echo "  Fix: Check if gunicorn is in requirements.txt"
echo "       Run: ./fix-dependencies.sh"
echo "       Rebuild: $COMPOSE_CMD -f docker-compose.working.yml build backend"
echo ""

echo -e "${YELLOW}Issue: YOLOE service failing${NC}"
echo "  Fix: Using mock service instead"
echo "       Check: http://localhost:8001/health"
echo ""

echo -e "${YELLOW}Issue: Permission denied errors${NC}"
echo "  Fix: If using Podman on Fedora, try:"
echo "       setsebool -P container_manage_cgroup true"
echo "       sudo setenforce 0  # Temporary, for testing only"
echo ""

# 8. Quick action menu
echo ""
echo -e "${BLUE}8. Quick Actions${NC}"
echo "----------------------------"
echo "What would you like to do?"
echo "  1) Stop all containers"
echo "  2) Start fresh (remove everything and restart)"
echo "  3) View backend logs"
echo "  4) Initialize database"
echo "  5) Test all services"
echo "  6) Exit"
echo ""
read -p "Select an option (1-6): " choice

case $choice in
    1)
        echo "Stopping all containers..."
        $COMPOSE_CMD -f docker-compose.working.yml down
        ;;
    2)
        echo "Starting fresh..."
        $COMPOSE_CMD -f docker-compose.working.yml down
        $CONTAINER_CMD system prune -f
        ./fix-dependencies.sh
        ./start-fixed.sh
        ;;
    3)
        echo "Viewing backend logs..."
        $COMPOSE_CMD -f docker-compose.working.yml logs -f backend
        ;;
    4)
        echo "Initializing database..."
        $CONTAINER_CMD exec -i movecrm-postgres psql -U movecrm -d movecrm < docs/database_schema_simple.sql
        ;;
    5)
        echo "Testing services..."
        ./test-services.sh
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        ;;
esac

echo ""
echo "========================================"
echo -e "${GREEN}Troubleshooting complete!${NC}"
echo "========================================"
echo ""
echo "If issues persist:"
echo "1. Check the full logs: $COMPOSE_CMD -f docker-compose.working.yml logs"
echo "2. Try the minimal setup: $COMPOSE_CMD -f docker-compose.minimal.yml up -d"
echo "3. Report specific error messages for more help"
