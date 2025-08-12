#!/bin/bash

# MoveCRM Widget Build Script
# This script minifies the widget for production deployment

set -e

echo "🔨 Building MoveCRM Widget..."

# Create dist directory
mkdir -p dist

# Copy source file to dist (for now, just copy - in production you'd minify)
echo "📦 Copying widget files..."
cp src/movecrm-widget.js dist/

# Create minified version (basic minification)
echo "🗜️  Creating minified version..."
if command -v uglifyjs &> /dev/null; then
    uglifyjs src/movecrm-widget.js -o dist/movecrm-widget.min.js -c -m
    echo "✅ Minified version created with UglifyJS"
else
    # Fallback: just copy and rename
    cp src/movecrm-widget.js dist/movecrm-widget.min.js
    echo "⚠️  UglifyJS not found, using unminified version"
fi

# Copy examples
echo "📋 Copying examples..."
cp -r examples dist/

# Create version info
echo "📝 Creating version info..."
cat > dist/version.json << EOF
{
  "version": "1.0.0",
  "build_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "git_commit": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
  "files": {
    "widget": "movecrm-widget.js",
    "widget_min": "movecrm-widget.min.js"
  }
}
EOF

# Calculate file sizes
echo "📊 File sizes:"
ls -lh dist/*.js | awk '{print "  " $9 ": " $5}'

echo "✅ Build complete! Files are in the dist/ directory"
echo ""
echo "🚀 To deploy:"
echo "  1. Upload dist/ contents to your CDN"
echo "  2. Update widget URLs in your applications"
echo "  3. Test the widget on your websites"

