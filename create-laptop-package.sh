#!/bin/bash

echo "📦 Creating MoveCRM Laptop Package"
echo "=================================="
echo ""

# Get the current directory name
PROJECT_DIR=$(basename "$PWD")
PACKAGE_NAME="movecrm-laptop-edition"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="${PACKAGE_NAME}_${TIMESTAMP}.tar.gz"

echo "📁 Project: $PROJECT_DIR"
echo "📦 Package: $ARCHIVE_NAME"
echo ""

# Create temporary directory for packaging
TEMP_DIR="/tmp/$PACKAGE_NAME"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

echo "📋 Copying project files..."

# Copy essential files and directories
cp -r backend "$TEMP_DIR/"
cp -r frontend "$TEMP_DIR/"
cp -r widget "$TEMP_DIR/"
cp -r yoloe-service "$TEMP_DIR/"
cp -r docs "$TEMP_DIR/"
cp -r postman "$TEMP_DIR/"

# Copy configuration files
cp docker-compose.yml "$TEMP_DIR/"
cp docker-compose.laptop.yml "$TEMP_DIR/"

# Copy documentation and setup scripts
cp README.md "$TEMP_DIR/"
cp README-LAPTOP.md "$TEMP_DIR/"
cp DELIVERABLES.md "$TEMP_DIR/"
cp setup-laptop.sh "$TEMP_DIR/"
cp setup-laptop.bat "$TEMP_DIR/"
cp my-test-page.html "$TEMP_DIR/"

# Create a quick start guide
cat > "$TEMP_DIR/QUICK-START.md" << 'EOF'
# 🚀 MoveCRM Laptop Edition - Quick Start

## Instant Setup (Choose your OS):

### Linux/macOS:
```bash
chmod +x setup-laptop.sh
./setup-laptop.sh
```

### Windows:
```cmd
setup-laptop.bat
```

## After Setup:
1. Open: `widget/examples/demo.html` in browser
2. Click the widget button and test!
3. Visit: http://localhost:3000 for dashboard

## Need Help?
- Read: `README-LAPTOP.md` for full guide
- Check: `README.md` for complete documentation

## System Requirements:
- Docker Desktop installed
- 4GB+ RAM (8GB recommended)
- 2GB+ free disk space

🎉 Enjoy your AI-powered moving CRM system!
EOF

# Create environment files from examples
if [ -f "backend/.env.example" ]; then
    cp "backend/.env.example" "$TEMP_DIR/backend/.env"
    echo "✅ Created backend/.env from example"
fi

if [ -f "yoloe-service/.env.example" ]; then
    cp "yoloe-service/.env.example" "$TEMP_DIR/yoloe-service/.env"
    echo "✅ Created yoloe-service/.env from example"
fi

# Make scripts executable
chmod +x "$TEMP_DIR/setup-laptop.sh"

echo ""
echo "🗜️  Creating archive..."

# Create the archive
cd /tmp
tar -czf "$ARCHIVE_NAME" "$PACKAGE_NAME"

# Move archive to current directory
mv "$ARCHIVE_NAME" "$OLDPWD/"

# Clean up
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Package created successfully!"
echo ""
echo "📦 Archive: $ARCHIVE_NAME"
echo "📏 Size: $(du -h "$ARCHIVE_NAME" | cut -f1)"
echo ""
echo "🚀 Transfer Instructions:"
echo "========================"
echo ""
echo "1. Copy '$ARCHIVE_NAME' to your laptop"
echo ""
echo "2. Extract on laptop:"
echo "   Linux/macOS: tar -xzf $ARCHIVE_NAME"
echo "   Windows: Use WinRAR/7-Zip to extract"
echo ""
echo "3. Run setup:"
echo "   Linux/macOS: cd $PACKAGE_NAME && ./setup-laptop.sh"
echo "   Windows: cd $PACKAGE_NAME && setup-laptop.bat"
echo ""
echo "4. Open demo: widget/examples/demo.html"
echo ""
echo "📋 What's Included:"
echo "  ✅ Complete MoveCRM system"
echo "  ✅ Laptop-optimized configuration"
echo "  ✅ Setup scripts for all platforms"
echo "  ✅ Demo files and examples"
echo "  ✅ Full documentation"
echo "  ✅ Postman API collection"
echo ""
echo "🎉 Ready to run on any laptop with Docker!"

# Display package contents
echo ""
echo "📁 Package Contents:"
echo "==================="
tar -tzf "$ARCHIVE_NAME" | head -20
if [ $(tar -tzf "$ARCHIVE_NAME" | wc -l) -gt 20 ]; then
    echo "   ... and $(expr $(tar -tzf "$ARCHIVE_NAME" | wc -l) - 20) more files"
fi

echo ""
echo "✨ Package complete! Transfer '$ARCHIVE_NAME' to your laptop and extract to get started!"
