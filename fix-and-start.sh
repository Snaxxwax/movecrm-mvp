#!/bin/bash

echo "🔧 Quick Fix - Starting Core Services"
echo "===================================="
echo ""

# Stop everything first
echo "🛑 Stopping all containers..."
podman-compose down 2>/dev/null

echo ""
echo "🚀 Starting essential services one by one..."

# Start database
echo "📊 Starting PostgreSQL..."
podman-compose up -d postgres
sleep 5

# Start Redis (already running but ensure it's up)
echo "🔴 Starting Redis..."
podman-compose up -d redis
sleep 2

# Start SuperTokens
echo "🔐 Starting SuperTokens..."
podman-compose up -d supertokens
sleep 10

# Start backend
echo "⚙️  Starting Backend..."
podman-compose up -d backend
sleep 10

# Start widget CDN
echo "🎨 Starting Widget CDN..."
podman-compose up -d widget-cdn
sleep 5

# Start MinIO (for file storage)
echo "💾 Starting MinIO..."
podman-compose up -d minio
sleep 5

echo ""
echo "🔍 Checking what's running..."
podman ps

echo ""
echo "🧪 Testing core services..."

# Test services
check_service() {
    local url=$1
    local name=$2
    
    echo -n "Testing $name... "
    if timeout 5 curl -s "$url" > /dev/null 2>&1; then
        echo "✅ Working"
    else
        echo "❌ Failed"
    fi
}

check_service "http://localhost:5000/health" "Backend"
check_service "http://localhost:8080" "Widget CDN"

echo ""
echo "📱 If Widget CDN is working, you can test:"
echo "   firefox widget/examples/demo.html"
echo ""
echo "🔧 To check logs if something failed:"
echo "   podman-compose logs backend"
echo "   podman-compose logs postgres"
echo "   podman-compose logs supertokens"
