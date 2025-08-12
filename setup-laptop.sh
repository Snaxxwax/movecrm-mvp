#!/bin/bash

echo "💻 MoveCRM Laptop Edition Setup"
echo "==============================="
echo ""

# Detect operating system
OS="Unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="Windows"
fi

echo "🖥️  Detected OS: $OS"
echo ""

# Check Docker installation
echo "🔍 Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed: $(docker --version)"
    
    # Check if Docker is running
    if docker info &> /dev/null; then
        echo "✅ Docker is running"
    else
        echo "⚠️  Docker is installed but not running"
        echo "   Please start Docker Desktop and try again"
        exit 1
    fi
else
    echo "❌ Docker is not installed"
    echo ""
    echo "📥 Please install Docker Desktop:"
    echo "   Windows/macOS: https://docker.com/products/docker-desktop"
    echo "   Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check Docker Compose
echo ""
echo "🔍 Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose is available: $(docker-compose --version)"
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    echo "✅ Docker Compose (plugin) is available: $(docker compose version)"
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose is not available"
    echo "   Please install Docker Compose"
    exit 1
fi

echo ""
echo "🚀 Starting MoveCRM on your laptop..."
echo "Using optimized configuration for laptop performance"
echo ""

# Use laptop-optimized compose file
if [ -f "docker-compose.laptop.yml" ]; then
    echo "📄 Using laptop-optimized configuration"
    $COMPOSE_CMD -f docker-compose.laptop.yml up -d --build
else
    echo "📄 Using standard configuration"
    $COMPOSE_CMD up -d --build
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
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $name is healthy"
            return 0
        else
            echo "⏳ $name starting... (attempt $attempt/$max_attempts)"
            sleep 5
            ((attempt++))
        fi
    done
    
    echo "❌ $name failed to start"
    return 1
}

check_service "http://localhost:5000/health" "Backend API"
check_service "http://localhost:8001/health" "YOLOE Service"
check_service "http://localhost:3000" "Frontend"
check_service "http://localhost:8080" "Widget CDN"

echo ""
echo "🎉 MoveCRM is running on your laptop!"
echo ""
echo "📱 Access Points:"
echo "   🖥️  CRM Dashboard:  http://localhost:3000"
echo "   📱 Widget Demo:     Open 'widget/examples/demo.html' in browser"
echo "   🔧 Backend API:     http://localhost:5000"
echo "   🤖 AI Service:      http://localhost:8001"
echo "   🗄️  Database Admin: http://localhost:8082"
echo "   💾 File Storage:    http://localhost:9001"
echo ""
echo "🧪 Quick Test:"
echo "   1. Open widget/examples/demo.html in your browser"
echo "   2. Click the floating 'Get Moving Quote' button"
echo "   3. Fill out the form and test file upload"
echo "   4. Submit and see the magic! ✨"
echo ""
echo "⚡ Laptop Performance Tips:"
echo "   • Close unnecessary applications while running"
echo "   • Docker Desktop should have 4GB+ memory allocated"
echo "   • Use 'docker-compose logs' to monitor if issues occur"
echo "   • Stop when not needed: docker-compose down"
echo ""
echo "🔧 Troubleshooting:"
echo "   • Port conflicts: Edit docker-compose.laptop.yml ports"
echo "   • Memory issues: Close other applications"
echo "   • Slow performance: Reduce max file sizes in config"
echo ""

# Check available system resources
echo "💻 System Resources:"
if command -v free &> /dev/null; then
    echo "   $(free -h | grep Mem)"
elif command -v vm_stat &> /dev/null; then
    # macOS
    echo "   Memory usage: $(vm_stat | head -4)"
else
    echo "   Check Task Manager/Activity Monitor for memory usage"
fi

echo ""
echo "✅ Setup complete! Enjoy testing your MoveCRM system! 🚀"
