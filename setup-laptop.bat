@echo off
title MoveCRM Laptop Setup for Windows

echo.
echo 💻 MoveCRM Laptop Edition Setup for Windows
echo =============================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed
    echo.
    echo 📥 Please install Docker Desktop for Windows:
    echo    https://docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Docker is installed
    docker --version
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Docker is installed but not running
    echo    Please start Docker Desktop and try again
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Docker is running
)

echo.
echo 🚀 Starting MoveCRM on your Windows laptop...
echo Using optimized configuration for laptop performance
echo.

REM Check if laptop config exists
if exist "docker-compose.laptop.yml" (
    echo 📄 Using laptop-optimized configuration
    docker-compose -f docker-compose.laptop.yml up -d --build
) else (
    echo 📄 Using standard configuration
    docker-compose up -d --build
)

echo.
echo ⏳ Waiting for services to start...
timeout /t 20 /nobreak >nul

echo.
echo 🔍 Checking service health...

REM Check services
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend API is healthy
) else (
    echo ⏳ Backend API is starting...
)

curl -s http://localhost:8001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ YOLOE Service is healthy
) else (
    echo ⏳ YOLOE Service is starting...
)

curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend is healthy
) else (
    echo ⏳ Frontend is starting...
)

echo.
echo 🎉 MoveCRM is running on your Windows laptop!
echo.
echo 📱 Access Points:
echo    🖥️  CRM Dashboard:  http://localhost:3000
echo    📱 Widget Demo:     Open 'widget\examples\demo.html' in browser
echo    🔧 Backend API:     http://localhost:5000
echo    🤖 AI Service:      http://localhost:8001
echo    🗄️  Database Admin: http://localhost:8082
echo    💾 File Storage:    http://localhost:9001
echo.
echo 🧪 Quick Test:
echo    1. Open widget\examples\demo.html in your browser
echo    2. Click the floating 'Get Moving Quote' button
echo    3. Fill out the form and test file upload
echo    4. Submit and see the magic! ✨
echo.
echo ⚡ Windows Laptop Tips:
echo    • Use PowerShell or Command Prompt
echo    • Ensure Windows Defender allows Docker
echo    • Check Docker Desktop memory allocation (4GB+)
echo    • Use 'docker-compose logs' to monitor
echo    • Stop when not needed: docker-compose down
echo.
echo 🔧 Troubleshooting:
echo    • Port conflicts: Edit docker-compose.laptop.yml
echo    • Firewall issues: Allow Docker in Windows Firewall
echo    • Performance: Close unnecessary applications
echo.
echo ✅ Setup complete! Press any key to open the demo page...
pause >nul

REM Try to open demo page
if exist "widget\examples\demo.html" (
    start "" "widget\examples\demo.html"
) else (
    echo Demo file not found. Please navigate to widget\examples\demo.html manually.
)

echo.
echo 🚀 Enjoy testing your MoveCRM system!
pause
