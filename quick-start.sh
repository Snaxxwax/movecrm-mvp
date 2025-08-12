#!/bin/bash

echo "🚀 Quick Start MoveCRM (Minimal Setup)"
echo "======================================"
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers..."
podman-compose down 2>/dev/null || true

echo ""
echo "📦 Starting core services first (without AI)..."
echo "This will get the widget working quickly!"
echo ""

# Start minimal services
podman-compose -f docker-compose.minimal.yml up -d --build

echo ""
echo "⏳ Waiting for core services..."
sleep 20

echo ""
echo "🔍 Testing core services..."

# Test core services
check_service() {
    local url=$1
    local name=$2
    
    echo -n "Testing $name... "
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ Working"
        return 0
    else
        echo "⏳ Starting..."
        return 1
    fi
}

check_service "http://localhost:5000/health" "Backend API"
check_service "http://localhost:3000" "Frontend"
check_service "http://localhost:8080" "Widget CDN"

echo ""
echo "🎉 Core MoveCRM is running!"
echo ""
echo "📱 You can now test the widget:"
echo "   firefox widget/examples/demo.html"
echo ""
echo "🖥️  Or visit the dashboard:"
echo "   firefox http://localhost:3000"
echo ""

# Ask if user wants to add AI service
echo "🤖 Do you want to start the AI detection service too?"
echo "   (This takes longer to build due to AI dependencies)"
echo ""
read -p "Start AI service? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧠 Starting AI service (this may take a few minutes)..."
    
    # Add the YOLOE service to the running setup
    podman-compose up -d --build yoloe-service
    
    echo ""
    echo "⏳ Waiting for AI service to build and start..."
    sleep 60
    
    if curl -s "http://localhost:8001/health" > /dev/null 2>&1; then
        echo "✅ AI service is ready!"
        echo "🎯 Full MoveCRM with AI detection is now running!"
    else
        echo "⚠️  AI service is still starting... check with:"
        echo "   podman-compose logs yoloe-service"
    fi
else
    echo ""
    echo "👍 No problem! Core MoveCRM is running."
    echo "   You can add AI later with: podman-compose up -d yoloe-service"
fi

echo ""
echo "🎮 Quick test commands:"
echo "   podman ps                    # Check running containers"
echo "   firefox widget/examples/demo.html  # Test widget"
echo "   firefox http://localhost:3000     # Dashboard"
echo ""
echo "✅ MoveCRM is ready for testing!"
