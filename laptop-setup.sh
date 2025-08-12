#!/bin/bash

echo "🚀 MoveCRM Laptop Setup Guide"
echo "================================"
echo ""

echo "📋 Step 1: System Requirements Check"
echo "------------------------------------"

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed: $(docker --version)"
else
    echo "❌ Docker is NOT installed"
    echo "   📥 Install Docker Desktop from: https://docker.com/products/docker-desktop"
    echo ""
fi

# Check if Docker Compose is available
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose is available: $(docker-compose --version)"
else
    echo "❌ Docker Compose is NOT available"
    echo "   📥 Install Docker Compose or use 'docker compose' (newer Docker versions)"
    echo ""
fi

# Check available memory
echo "💾 Available Memory:"
free -h 2>/dev/null || echo "   Use 'Task Manager' or 'Activity Monitor' to check RAM"

# Check available disk space
echo "💽 Available Disk Space:"
df -h . 2>/dev/null || echo "   Check available disk space (need at least 2GB)"

echo ""
echo "📁 Step 2: Project Transfer Options"
echo "-----------------------------------"
echo ""
echo "Option A: Copy via USB/External Drive"
echo "   1. Copy entire 'movecrm-mvp' folder to USB drive"
echo "   2. Transfer to laptop"
echo "   3. Extract and run"
echo ""
echo "Option B: Git Repository (recommended)"
echo "   1. Create Git repository"
echo "   2. Push to GitHub/GitLab"
echo "   3. Clone on laptop"
echo ""
echo "Option C: Archive and Transfer"
echo "   1. Create archive: tar -czf movecrm-mvp.tar.gz movecrm-mvp/"
echo "   2. Transfer archive to laptop"
echo "   3. Extract: tar -xzf movecrm-mvp.tar.gz"
echo ""

echo "🚀 Step 3: Running on Laptop"
echo "-----------------------------"
echo "Once transferred, run these commands:"
echo ""
echo "cd movecrm-mvp"
echo "chmod +x start-project.sh test-system.sh  # (Linux/macOS only)"
echo "docker-compose up -d --build"
echo ""
echo "Access URLs:"
echo "🖥️  Frontend:     http://localhost:3000"
echo "📱 Widget Demo:  Open widget/examples/demo.html"
echo "🔧 Backend API:  http://localhost:5000"
echo "🤖 AI Service:   http://localhost:8001"
echo ""

echo "⚡ Performance Tips for Laptops"
echo "--------------------------------"
echo "• Close unnecessary applications"
echo "• Ensure Docker has enough memory allocated (4GB+)"
echo "• Use 'docker-compose up' without -d to see logs"
echo "• Stop services when not in use: docker-compose down"
echo ""

echo "🔧 Laptop-Specific Configurations"
echo "----------------------------------"
echo "• Windows: Use PowerShell or WSL2"
echo "• macOS: Terminal works perfectly"
echo "• Linux: Native Docker support"
echo ""

echo "✅ Setup complete! Transfer the project and run 'docker-compose up -d --build'"
