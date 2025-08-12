#!/bin/bash

echo "🐧 MoveCRM on Fedora with Podman"
echo "================================="
echo ""

# Check if Podman is installed
if command -v podman &> /dev/null; then
    echo "✅ Podman is installed: $(podman --version)"
else
    echo "❌ Podman is not installed"
    echo "   Installing Podman on Fedora..."
    sudo dnf install -y podman podman-compose
    echo "✅ Podman installed!"
fi

# Check if podman-compose is available
if command -v podman-compose &> /dev/null; then
    echo "✅ podman-compose is available: $(podman-compose --version)"
    COMPOSE_CMD="podman-compose"
elif command -v docker-compose &> /dev/null; then
    echo "✅ docker-compose found, configuring for Podman..."
    export DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock
    COMPOSE_CMD="docker-compose"
else
    echo "❌ No compose tool found"
    echo "   Installing podman-compose..."
    sudo dnf install -y podman-compose
    COMPOSE_CMD="podman-compose"
fi

echo ""
echo "🔧 Setting up Podman for MoveCRM..."

# Start Podman socket for compose compatibility
systemctl --user enable --now podman.socket
export DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock

# Create podman-specific network if needed
podman network exists movecrm-network || podman network create movecrm-network

echo ""
echo "🚀 Starting MoveCRM with Podman..."
echo "Using compose command: $COMPOSE_CMD"
echo ""

# Use podman-compose or docker-compose with podman socket
if [ "$COMPOSE_CMD" = "podman-compose" ]; then
    $COMPOSE_CMD -f docker-compose.yml up -d --build
else
    # Use docker-compose with podman socket
    DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock $COMPOSE_CMD up -d --build
fi

echo ""
echo "⏳ Waiting for services to start..."
sleep 20

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
echo "🎉 MoveCRM is running with Podman!"
echo ""
echo "📱 Access Points:"
echo "   🖥️  CRM Dashboard:  http://localhost:3000"
echo "   📱 Widget Demo:     firefox widget/examples/demo.html"
echo "   🔧 Backend API:     http://localhost:5000"
echo "   🤖 AI Service:      http://localhost:8001"
echo "   🗄️  Database Admin: http://localhost:8082"
echo "   💾 File Storage:    http://localhost:9001"
echo ""
echo "🧪 Quick Test Commands:"
echo "   podman ps                          # View running containers"
echo "   $COMPOSE_CMD logs backend         # View backend logs"
echo "   $COMPOSE_CMD logs yoloe-service   # View AI service logs"
echo "   $COMPOSE_CMD down                 # Stop all services"
echo ""
echo "🔧 Podman-specific commands:"
echo "   podman pod ls                      # List pods"
echo "   podman images                      # List images"
echo "   podman system prune                # Clean up unused resources"
echo ""
echo "✅ Ready to test! Open the widget demo with:"
echo "   firefox widget/examples/demo.html"
