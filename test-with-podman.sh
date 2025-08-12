#!/bin/bash

echo "🧪 Testing MoveCRM with Podman"
echo "=============================="
echo ""

# Check if services are running
echo "🔍 Checking container status..."
echo ""

# List MoveCRM containers
echo "📋 MoveCRM containers:"
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(movecrm|postgres|redis|supertokens|minio|adminer)" || echo "   No MoveCRM containers running"

echo ""

# Check individual services
echo "🩺 Health check tests..."

# Function to test service
test_service() {
    local url=$1
    local name=$2
    local expected=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -w "%{http_code}" -o /tmp/test_response "$url" 2>/dev/null)
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ] || [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
        if [ -n "$expected" ]; then
            if grep -q "$expected" /tmp/test_response 2>/dev/null; then
                echo "✅ Healthy (HTTP $http_code, contains '$expected')"
            else
                echo "⚠️  HTTP $http_code but response doesn't contain '$expected'"
            fi
        else
            echo "✅ Healthy (HTTP $http_code)"
        fi
    else
        echo "❌ Failed (HTTP $http_code)"
    fi
}

# Test all services
test_service "http://localhost:5000/health" "Backend API" "healthy"
test_service "http://localhost:8001/health" "YOLOE Service" "healthy"
test_service "http://localhost:3000" "Frontend" ""
test_service "http://localhost:8080" "Widget CDN" ""
test_service "http://localhost:8082" "Database Admin" ""
test_service "http://localhost:9001" "MinIO Console" ""

echo ""

# Test API endpoints
echo "🔗 API endpoint tests..."

# Test public quote endpoint
echo -n "Testing public quote endpoint... "
response=$(curl -s -X POST "http://localhost:5000/api/public/quote" \
    -H "X-Tenant-Slug: demo" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test User","email":"test@example.com","pickup_address":"123 Test St","delivery_address":"456 Test Ave"}' \
    -w "%{http_code}")

http_code="${response: -3}"
if [[ "$http_code" =~ ^[24][0-9][0-9]$ ]]; then
    echo "✅ Working (HTTP $http_code)"
else
    echo "⚠️  HTTP $http_code (may need authentication setup)"
fi

echo ""

# Database connection test
echo "🗄️  Database tests..."
echo -n "Testing PostgreSQL connection... "
if podman exec -it movecrm-postgres-laptop psql -U movecrm -d movecrm -c "SELECT 1;" &>/dev/null 2>&1 || \
   podman exec -it movecrm-postgres psql -U movecrm -d movecrm -c "SELECT 1;" &>/dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "⚠️  Connection issues"
fi

echo ""

# Redis test
echo "🔴 Redis tests..."
echo -n "Testing Redis connection... "
if podman exec -it movecrm-redis-laptop redis-cli ping &>/dev/null 2>&1 || \
   podman exec -it movecrm-redis redis-cli ping &>/dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "⚠️  Connection issues"
fi

echo ""

# File system tests
echo "📁 File system tests..."
echo -n "Testing uploads directory... "
if podman exec movecrm-backend-laptop ls /app/uploads &>/dev/null 2>&1 || \
   podman exec movecrm-backend ls /app/uploads &>/dev/null 2>&1; then
    echo "✅ Accessible"
else
    echo "⚠️  Issues accessing uploads"
fi

echo ""

# Widget file test
echo "🎨 Widget tests..."
if [ -f "widget/examples/demo.html" ]; then
    echo "✅ Widget demo file exists"
    echo "   To test: firefox widget/examples/demo.html"
else
    echo "❌ Widget demo file not found"
fi

if [ -f "widget/dist/movecrm-widget.js" ] || [ -f "widget/src/movecrm-widget.js" ]; then
    echo "✅ Widget JavaScript file exists"
else
    echo "⚠️  Widget JavaScript file not found"
fi

echo ""

# Logs test
echo "📋 Recent logs..."
echo "Backend logs (last 5 lines):"
if podman logs movecrm-backend-laptop --tail 5 2>/dev/null || podman logs movecrm-backend --tail 5 2>/dev/null; then
    echo "✅ Backend logs accessible"
else
    echo "⚠️  Cannot access backend logs"
fi

echo ""
echo "YOLOE logs (last 5 lines):"
if podman logs movecrm-yoloe-laptop --tail 5 2>/dev/null || podman logs movecrm-yoloe --tail 5 2>/dev/null; then
    echo "✅ YOLOE logs accessible"
else
    echo "⚠️  Cannot access YOLOE logs"
fi

echo ""

# Performance check
echo "⚡ Performance check..."
echo "Container resource usage:"
podman stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | head -10 || echo "   Statistics not available"

echo ""
echo "🎉 Testing complete!"
echo ""
echo "📱 Next steps:"
echo "   1. Open widget demo: firefox widget/examples/demo.html"
echo "   2. Visit dashboard: firefox http://localhost:3000"
echo "   3. Check API docs: curl http://localhost:5000/health"
echo ""
echo "🔧 Useful Podman commands:"
echo "   podman ps                    # List running containers"
echo "   podman logs <container>      # View container logs"
echo "   podman exec -it <container> bash  # Enter container"
echo "   podman-compose down          # Stop all services"
echo ""
echo "🚨 If issues found:"
echo "   podman-compose logs          # View all logs"
echo "   podman system prune          # Clean up resources"
echo "   ./start-with-podman.sh       # Restart services"

# Clean up temp file
rm -f /tmp/test_response
