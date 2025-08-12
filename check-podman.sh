#!/bin/bash

echo "🔍 Podman System Check for MoveCRM"
echo "=================================="
echo ""

# Check Podman installation
echo "📦 Checking Podman installation..."
if command -v podman &> /dev/null; then
    echo "✅ Podman is installed"
    podman --version
    echo ""
    
    # Check Podman info
    echo "ℹ️  Podman system info:"
    podman info --format "{{.Host.Os}} {{.Host.Arch}} - {{.Host.Distribution.Distribution}} {{.Host.Distribution.Version}}"
    echo "   Storage Driver: $(podman info --format "{{.Store.GraphDriverName}}")"
    echo "   Root: $(podman info --format "{{.Store.GraphRoot}}")"
    echo ""
else
    echo "❌ Podman is not installed"
    echo "   To install on Fedora:"
    echo "   sudo dnf install -y podman podman-compose"
    exit 1
fi

# Check for compose tools
echo "🔧 Checking compose tools..."
if command -v podman-compose &> /dev/null; then
    echo "✅ podman-compose is available"
    podman-compose --version
    COMPOSE_TOOL="podman-compose"
elif command -v docker-compose &> /dev/null; then
    echo "✅ docker-compose found (can work with Podman)"
    docker-compose --version
    COMPOSE_TOOL="docker-compose"
else
    echo "❌ No compose tool found"
    echo "   Installing podman-compose..."
    sudo dnf install -y podman-compose
    COMPOSE_TOOL="podman-compose"
fi

echo ""

# Check if Podman socket is running (needed for docker-compose compatibility)
echo "🔌 Checking Podman socket..."
if systemctl --user is-active --quiet podman.socket; then
    echo "✅ Podman socket is running"
else
    echo "⚡ Starting Podman socket..."
    systemctl --user enable --now podman.socket
    if systemctl --user is-active --quiet podman.socket; then
        echo "✅ Podman socket started successfully"
    else
        echo "❌ Failed to start Podman socket"
    fi
fi

echo ""

# Check existing containers/pods
echo "📋 Current Podman state..."
CONTAINERS=$(podman ps -a --format "{{.Names}}" | grep -E "(movecrm|postgres|redis)" | wc -l)
if [ $CONTAINERS -gt 0 ]; then
    echo "⚠️  Found existing MoveCRM containers:"
    podman ps -a --format "table {{.Names}}\t{{.Status}}" | grep -E "(movecrm|postgres|redis)"
    echo ""
    echo "🧹 To clean up old containers:"
    echo "   podman stop \$(podman ps -aq --filter name=movecrm)"
    echo "   podman rm \$(podman ps -aq --filter name=movecrm)"
    echo ""
else
    echo "✅ No existing MoveCRM containers found"
fi

# Check networks
echo "🌐 Checking networks..."
if podman network exists movecrm-network; then
    echo "✅ movecrm-network exists"
else
    echo "🔧 Creating movecrm-network..."
    podman network create movecrm-network
    echo "✅ Network created"
fi

echo ""

# Check available ports
echo "🔌 Checking required ports..."
PORTS=(3000 5000 8001 8080 5432 6379 3567 8082 9000 9001)
for port in "${PORTS[@]}"; do
    if ss -tuln | grep -q ":$port "; then
        echo "⚠️  Port $port is in use"
    else
        echo "✅ Port $port is available"
    fi
done

echo ""

# System resources
echo "💻 System resources..."
echo "   RAM: $(free -h | awk '/^Mem:/ {print $2 " total, " $3 " used, " $7 " available"}')"
echo "   Disk: $(df -h . | awk 'NR==2 {print $4 " available"}')"

echo ""
echo "🚀 Ready to start MoveCRM with Podman!"
echo ""
echo "💡 Recommended startup command:"
echo "   ./start-with-podman.sh"
echo ""
echo "🔧 Alternative manual commands:"
echo "   Export socket: export DOCKER_HOST=unix:///run/user/\$UID/podman/podman.sock"
if [ "$COMPOSE_TOOL" = "podman-compose" ]; then
    echo "   Start services: podman-compose up -d --build"
else
    echo "   Start services: docker-compose up -d --build"
fi
echo "   Check status: podman ps"
echo ""
echo "📱 After startup, test with:"
echo "   firefox widget/examples/demo.html"
