# 💻 MoveCRM Laptop Edition

Run your complete MoveCRM system on any laptop! This guide will get you up and running in minutes.

## 🚀 Quick Start

### For Linux/macOS:
```bash
chmod +x setup-laptop.sh
./setup-laptop.sh
```

### For Windows:
```cmd
setup-laptop.bat
```

## 📋 Requirements

**Minimum:**
- **RAM:** 4GB (8GB recommended)
- **Storage:** 2GB free space
- **Docker:** Docker Desktop installed

## 🔧 Installation Steps

### 1. Install Docker Desktop
- **Windows/macOS:** https://docker.com/products/docker-desktop
- **Linux:** https://docs.docker.com/engine/install/

### 2. Get the Project
Choose one method:

**Option A: Copy from USB/Drive**
```bash
# Copy the entire movecrm-mvp folder to your laptop
# Then run the setup script
```

**Option B: Download Archive**
```bash
# Extract the project archive
tar -xzf movecrm-mvp.tar.gz  # Linux/macOS
# Or use extraction software on Windows
```

**Option C: Git Clone** (if available)
```bash
git clone <your-repository-url>
cd movecrm-mvp
```

### 3. Run Setup Script
The setup script will:
- ✅ Check system requirements
- ✅ Start all services optimized for laptops
- ✅ Verify everything is working
- ✅ Open demo page

## 🎯 What You Get

### 🖥️ **CRM Dashboard** - http://localhost:3000
- Modern React interface
- Quote management
- Customer database
- Pricing configuration
- Brand settings

### 📱 **Widget Demo** - Open `widget/examples/demo.html`
- Beautiful demo website
- Embeddable quote widget
- File upload testing
- Form validation

### 🤖 **AI Detection** - http://localhost:8001
- YOLOE item recognition
- Automatic pricing
- Photo analysis

### 🗄️ **Database Admin** - http://localhost:8082
- PostgreSQL management
- Data viewing/editing
- Login: postgres/movecrm/movecrm_dev

### 💾 **File Storage** - http://localhost:9001
- MinIO console
- File management
- Login: devuser/devpass123

## 🧪 Testing Guide

### 1. **Widget Test (Most Fun!)**
1. Open `widget/examples/demo.html` in browser
2. Click floating "Get Moving Quote" button
3. Fill form with test data:
   ```
   Name: John Smith
   Email: john@example.com
   Phone: (555) 123-4567
   Pickup: 123 Main St
   Delivery: 456 Oak Ave
   ```
4. Upload furniture photos
5. Submit and watch AI analysis!

### 2. **Custom Page Test**
1. Open `my-test-page.html` in browser
2. Test widget with custom styling
3. Try different configurations

### 3. **API Testing**
1. Import Postman collection from `postman/` folder
2. Test all endpoints
3. Upload images for AI detection

## ⚡ Laptop Optimization

The laptop edition includes:
- **Reduced Memory Usage** - Optimized PostgreSQL settings
- **CPU-Only AI** - No GPU required for YOLOE
- **Smaller File Limits** - 25MB vs 50MB for better performance
- **Fewer Concurrent Jobs** - Prevents laptop overload
- **Lightweight Redis** - Memory-optimized caching

## 🔧 Troubleshooting

### Services Won't Start?
```bash
# Check Docker status
docker info

# View service logs
docker-compose logs backend
docker-compose logs yoloe-service

# Restart everything
docker-compose down
docker-compose up -d --build
```

### Port Conflicts?
Edit `docker-compose.laptop.yml` and change ports:
```yaml
ports:
  - "3001:3000"  # Frontend on port 3001
  - "5001:5000"  # Backend on port 5001
```

### Performance Issues?
- Close unnecessary applications
- Increase Docker Desktop memory allocation (Settings > Resources)
- Use smaller test images
- Reduce concurrent processing

### Widget Not Loading?
1. Check http://localhost:8080 loads
2. Clear browser cache
3. Check browser console for errors
4. Verify CORS settings

## 💡 Development Tips

### Stop Services When Not Needed
```bash
docker-compose down
```

### View Real-time Logs
```bash
docker-compose logs -f backend
docker-compose logs -f yoloe-service
```

### Update Code
```bash
# Rebuild after code changes
docker-compose up -d --build
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U movecrm -d movecrm

# View tables
\dt

# Check quotes
SELECT * FROM quotes LIMIT 5;
```

## 🌟 What Makes This Special

✅ **Complete SaaS System** - Multi-tenant CRM for moving companies  
✅ **AI-Powered Quotes** - Upload photos, get instant pricing  
✅ **Embeddable Widget** - Add to any website  
✅ **Production Ready** - Security, monitoring, scaling  
✅ **Laptop Optimized** - Runs smoothly on any laptop  

## 🚀 Next Steps

1. **Customize the Widget** - Edit colors, branding, features
2. **Add Your Data** - Import real moving company data
3. **Test with Real Photos** - Upload furniture/room photos
4. **Deploy to Cloud** - Scale to production when ready
5. **Build Your Business** - Market to moving companies!

---

## 🎉 You're Ready!

Your MoveCRM system is now running on your laptop. This is a complete, production-ready SaaS platform that could power real moving companies!

**Have fun testing and feel free to customize everything!** 🚀

---

*Need help? Check the main README.md or create an issue.*
