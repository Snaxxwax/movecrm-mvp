#!/bin/bash

echo "🧪 Testing MoveCRM System..."

# Function to check if service is healthy
check_service() {
    local url=$1
    local name=$2
    
    echo -n "Checking $name... "
    if curl -s "$url" > /dev/null; then
        echo "✅ Healthy"
        return 0
    else
        echo "❌ Failed"
        return 1
    fi
}

# Wait for services to start
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "🔍 Testing Service Health:"
check_service "http://localhost:5000/health" "Backend API"
check_service "http://localhost:8001/health" "YOLOE Service" 
check_service "http://localhost:3000" "Frontend"
check_service "http://localhost:8080" "Widget CDN"

echo ""
echo "🧪 Testing API Endpoints:"

# Test backend health
echo -n "Backend API health... "
response=$(curl -s http://localhost:5000/health)
if [[ $response == *"healthy"* ]]; then
    echo "✅ Healthy"
else
    echo "❌ Failed: $response"
fi

# Test YOLOE service health
echo -n "YOLOE service health... "
response=$(curl -s http://localhost:8001/health)
if [[ $response == *"healthy"* ]]; then
    echo "✅ Healthy"
else
    echo "❌ Failed: $response"
fi

echo ""
echo "📱 Testing Widget:"
echo "1. Open: widget/examples/demo.html in your browser"
echo "2. Click the floating 'Get Moving Quote' button"
echo "3. Fill out the form and submit"

echo ""
echo "🖥️  Testing Dashboard:"
echo "1. Open: http://localhost:3000"
echo "2. Login with demo credentials (if implemented)"

echo ""
echo "🗄️  Database Access:"
echo "1. Open: http://localhost:8082 (Adminer)"
echo "2. Login with:"
echo "   - System: PostgreSQL"
echo "   - Server: postgres"
echo "   - Username: movecrm"
echo "   - Password: movecrm_password"
echo "   - Database: movecrm"

echo ""
echo "💾 File Storage:"
echo "1. Open: http://localhost:9001 (MinIO Console)"
echo "2. Login with:"
echo "   - Username: minioadmin"
echo "   - Password: minioadmin123"

echo ""
echo "🎉 Testing Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Import the Postman collection from postman/ folder"
echo "2. Test API endpoints with Postman"
echo "3. Upload test images to test AI detection"
echo "4. Customize the widget for your needs"
