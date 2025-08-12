#!/bin/bash

# Make this script executable: chmod +x start-project.sh

echo "🚀 Starting MoveCRM MVP Project..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

cd "$(dirname "$0")"

echo "📦 Building and starting all services..."
docker-compose up -d --build

echo "⏳ Waiting for services to be healthy..."
sleep 10

echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "🎉 MoveCRM is starting up! You can access:"
echo ""
echo "🖥️  Frontend Dashboard: http://localhost:3000"
echo "🔗 Backend API:        http://localhost:5000"
echo "🤖 YOLOE Service:      http://localhost:8001"
echo "🎨 Widget CDN:         http://localhost:8080"
echo "🗄️  Database Admin:    http://localhost:8082"
echo "💾 File Storage:       http://localhost:9001"
echo ""
echo "📱 Widget Demo:        Open widget/examples/demo.html in your browser"
echo ""
echo "✅ To test the system, run: ./test-system.sh"
