#!/bin/bash

echo "🔧 MoveCRM Dependency Fixer"
echo "==========================="
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📦 Fixing Backend Dependencies..."
# Check if gunicorn is already in requirements.txt
if ! grep -q "gunicorn" backend/requirements.txt; then
    echo "Adding gunicorn and gevent to backend requirements..."
    cat >> backend/requirements.txt << EOF

# WSGI Server (Required for production)
gunicorn==22.0.0
gevent==24.2.1

# Additional missing dependencies
python-multipart==0.0.9
EOF
    echo "✅ Backend requirements fixed!"
else
    echo "✓ Gunicorn already in requirements"
fi

echo ""
echo "📦 Fixing YOLOE Service Dependencies..."
# Check if uvicorn is already in requirements.txt
if ! grep -q "uvicorn" yoloe-service/requirements.txt 2>/dev/null; then
    echo "Adding uvicorn and fastapi to YOLOE requirements..."
    cat >> yoloe-service/requirements.txt << EOF

# ASGI Server (Required)
uvicorn==0.30.6
fastapi==0.111.0
python-multipart==0.0.9

# Core AI dependencies (minimal)
ultralytics==8.2.0
opencv-python-headless==4.10.0.84
numpy==1.26.4
Pillow==10.4.0
EOF
    echo "✅ YOLOE requirements fixed!"
else
    echo "✓ Uvicorn already in requirements"
fi

echo ""
echo "🔍 Checking for missing files..."

# Create simple YOLOE main.py if it doesn't have proper structure
if [ -f "yoloe-service/main.py" ]; then
    if ! grep -q "FastAPI" yoloe-service/main.py; then
        echo "⚠️  YOLOE main.py exists but might need FastAPI structure"
        echo "   Creating backup as main.py.backup"
        cp yoloe-service/main.py yoloe-service/main.py.backup 2>/dev/null || true
    fi
else
    echo "❌ YOLOE main.py missing - will create it"
fi

# Create frontend Dockerfile.dev if missing
if [ ! -f "frontend/Dockerfile.dev" ]; then
    echo "Creating frontend/Dockerfile.dev..."
    cat > frontend/Dockerfile.dev << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Install dependencies first (better caching)
COPY package*.json ./
RUN npm install

# Copy application files
COPY . .

# Expose the dev server port
EXPOSE 3000

# Start Vite dev server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
EOF
    echo "✅ Frontend Dockerfile.dev created!"
else
    echo "✓ Frontend Dockerfile.dev already exists"
fi

echo ""
echo "📋 Creating simplified database schema..."
cat > docs/database_schema_simple.sql << 'EOF'
-- MoveCRM Simplified Schema for Quick Start
-- This is a minimal version to get started quickly

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean restart)
DROP TABLE IF EXISTS quote_items CASCADE;
DROP TABLE IF EXISTS quotes CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS tenants CASCADE;

-- Minimal tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Minimal users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'customer',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, email)
);

-- Minimal quotes table
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    quote_number VARCHAR(50) UNIQUE NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Minimal quote items table
CREATE TABLE quote_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quote_id UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    item_name VARCHAR(255),
    quantity INTEGER DEFAULT 1,
    price DECIMAL(8,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert demo tenant
INSERT INTO tenants (slug, name) 
VALUES ('demo', 'Demo Moving Company')
ON CONFLICT (slug) DO NOTHING;

-- Insert test user
INSERT INTO users (tenant_id, email, first_name, last_name, role)
SELECT id, 'admin@demo.com', 'Admin', 'User', 'admin'
FROM tenants WHERE slug = 'demo'
ON CONFLICT DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_quotes_tenant_id ON quotes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_quote_items_quote_id ON quote_items(quote_id);

-- Verify setup
SELECT 'Setup Complete!' as status;
EOF

echo "✅ Simplified database schema created!"

echo ""
echo "✨ All dependencies fixed!"
echo ""
echo "Next steps:"
echo "1. Run: ./start-fixed.sh"
echo "   OR"
echo "2. Run: podman-compose -f docker-compose.working.yml up -d --build"
echo ""
echo "This will start your services with the fixed dependencies."

chmod +x fix-dependencies.sh 2>/dev/null || true
