#!/bin/bash

echo "🔧 Fixed Dependencies - Restarting MoveCRM"
echo "=========================================="
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers..."
podman-compose down 2>/dev/null || true

# Clean up failed builds
echo "🧹 Cleaning up failed builds..."
podman system prune -f

echo ""
echo "🚀 Starting MoveCRM with fixed dependencies..."
podman-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 30

echo ""
echo "🔍 Checking service health..."

# Function to check service health
check_service() {
    local url=$1
    local name=$2
    
    echo -n "Checking $name... "
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ Healthy"
    else
        echo "⏳ Starting..."
    fi
}

check_service "http://localhost:5000/health" "Backend API"
check_service "http://localhost:8001/health" "YOLOE Service" 
check_service "http://localhost:3000" "Frontend"
check_service "http://localhost:8080" "Widget CDN"

echo ""
echo "🎉 MoveCRM restarted! Check status:"
echo "   podman ps"
echo ""
echo "📱 Test the widget:"
echo "   firefox widget/examples/demo.html"
