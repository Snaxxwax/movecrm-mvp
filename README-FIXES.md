# MoveCRM Quick Fix Guide

## 🚀 Quick Start (Fixed Version)

I've created several scripts to fix and run your MoveCRM project. Here's how to use them:

### Step 1: Make Scripts Executable
```bash
cd ~/claude-desktop-fedora/movecrm-mvp-complete/movecrm-mvp
chmod +x *.sh
```

### Step 2: Fix Dependencies (Required First Time)
```bash
./fix-dependencies.sh
```
This script:
- Adds missing `gunicorn` and `gevent` to backend requirements
- Adds missing `uvicorn` and `fastapi` to YOLOE requirements  
- Creates missing frontend Dockerfile.dev
- Creates simplified database schema

### Step 3: Start Everything
```bash
./start-fixed.sh
```
This script:
- Runs the dependency fix
- Starts all services using the working docker-compose
- Initializes the database with simple schema
- Shows you the status and access URLs

### Step 4: Test Services
```bash
./test-services.sh
```
This verifies:
- All containers are running
- APIs are responding
- Database is connected
- Mock YOLOE detection works

### Step 5: If Something Goes Wrong
```bash
./troubleshoot.sh
```
Interactive troubleshooter that:
- Checks for common issues
- Offers quick fixes
- Shows container logs
- Provides action menu

## 📁 Files Created

### Core Fix Scripts
- `fix-dependencies.sh` - Fixes all missing dependencies
- `start-fixed.sh` - Main startup script with all fixes
- `test-services.sh` - Comprehensive service tester
- `troubleshoot.sh` - Interactive troubleshooting helper

### Configuration Files
- `docker-compose.working.yml` - Simplified, working Docker Compose
- `docs/database_schema_simple.sql` - Minimal database schema
- `yoloe-service/main_mock.py` - Mock YOLOE service for development
- `frontend/Dockerfile.dev` - Missing frontend Dockerfile

## 🎯 What's Fixed

### ✅ Backend Issues
- Added missing `gunicorn` and `gevent` to requirements.txt
- Simplified startup to use Flask dev server instead of complex gunicorn
- Fixed import paths and dependencies

### ✅ Database Issues  
- Created simplified schema without complex triggers/RLS
- Fixed permission issues with init scripts
- Added proper health checks

### ✅ YOLOE Service Issues
- Created mock service that works without actual AI models
- Added missing `uvicorn` and `fastapi` dependencies
- Returns fake detection results for testing

### ✅ Frontend Issues
- Created missing Dockerfile.dev
- Added proper volume mounts
- Fixed Vite dev server configuration

## 🌐 Access Points

After running `./start-fixed.sh`, you can access:

- **Backend API**: http://localhost:5000
- **YOLOE Mock**: http://localhost:8001  
- **Widget CDN**: http://localhost:8080
- **MinIO Console**: http://localhost:9001
  - Username: `minioadmin`
  - Password: `minioadmin123`
- **Database Admin**: http://localhost:8082
  - Server: `postgres`
  - Username: `movecrm`
  - Password: `movecrm_password`
  - Database: `movecrm`

## 🧪 Quick Tests

### Test Backend Health
```bash
curl http://localhost:5000/health
```

### Test YOLOE Mock
```bash
curl http://localhost:8001/health
```

### Test Mock Detection
```bash
curl -X POST http://localhost:8001/detect/text \
  -H "Content-Type: application/json" \
  -d '{"description": "sofa and table"}'
```

### View Logs
```bash
podman-compose -f docker-compose.working.yml logs -f backend
```

## 🛑 Stop Everything
```bash
podman-compose -f docker-compose.working.yml down
```

## 💡 Next Steps

Once everything is running locally:

1. **Test Core Features**
   - Verify widget embedding works
   - Test quote creation API
   - Check database operations

2. **Prepare for Deployment**
   - Remove YOLOE service (use external AI API)
   - Combine frontend + backend into single service
   - Switch to managed PostgreSQL

3. **Deploy to Cloud**
   - Railway/Render for simple deployment (~$35/month)
   - Or continue local development

## ⚠️ Troubleshooting

### If containers won't start:
```bash
podman-compose -f docker-compose.working.yml down
podman system prune -f
./start-fixed.sh
```

### If database has errors:
```bash
podman exec -i movecrm-postgres psql -U movecrm -d movecrm < docs/database_schema_simple.sql
```

### If backend won't build:
```bash
./fix-dependencies.sh
podman-compose -f docker-compose.working.yml build --no-cache backend
```

### For Fedora permission issues:
```bash
# Temporary for testing
sudo setenforce 0

# Or permanently allow containers
setsebool -P container_manage_cgroup true
```

## 📞 Getting Help

If issues persist after running the troubleshoot script:
1. Check full logs: `podman-compose -f docker-compose.working.yml logs`
2. Look for specific error messages
3. Try the minimal setup: `docker-compose.minimal.yml`

## 🎉 Success Indicators

You know everything is working when:
- `./test-services.sh` shows all services green
- http://localhost:8080 shows the widget page
- http://localhost:5000/health returns `{"status": "healthy"}`
- No error messages in container logs
