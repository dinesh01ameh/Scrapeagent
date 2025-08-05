@echo off
REM SwissKnife AI Scraper - Docker Launch Script (Windows)
REM Complete containerized deployment script

echo 🐳 SwissKnife AI Scraper - Docker Launch
echo ========================================

REM Function to check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)
echo ✅ Docker is running

REM Function to check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose and try again.
    pause
    exit /b 1
)
echo ✅ Docker Compose is available

REM Handle script arguments
set mode=%1
if "%mode%"=="" set mode=default

if "%mode%"=="dev" goto development
if "%mode%"=="development" goto development
if "%mode%"=="prod" goto production
if "%mode%"=="production" goto production
if "%mode%"=="logs" goto logs
if "%mode%"=="stop" goto stop
if "%mode%"=="status" goto status
if "%mode%"=="help" goto help
if "%mode%"=="-h" goto help
if "%mode%"=="--help" goto help
goto default

:development
echo.
echo 🚀 Launching SwissKnife AI Scraper in development mode...
echo 📦 Building and starting development environment...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
goto show_status

:production
echo.
echo 🚀 Launching SwissKnife AI Scraper in production mode...
echo 📦 Building and starting production environment...
docker-compose -f docker-compose.prod.yml up --build -d
goto show_status

:default
echo.
echo 🚀 Launching SwissKnife AI Scraper in default mode...
echo 📦 Building and starting default environment...
docker-compose up --build -d
goto show_status

:show_status
echo.
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

echo.
echo 📊 Service Status:
docker-compose ps

echo.
echo 🌐 Access URLs:
echo   Frontend Dashboard: http://localhost:8650
echo   Backend API:        http://localhost:8601
echo   API Documentation:  http://localhost:8601/docs
echo   PostgreSQL:         localhost:5432
echo   Redis:              localhost:6379
echo   Ollama:             http://localhost:11434

echo.
echo 🎉 SwissKnife AI Scraper is now running!
echo.
echo 📝 Useful commands:
echo   View logs:     docker-compose logs -f
echo   Stop services: docker-compose down
echo   Restart:       docker-compose restart
echo   Shell access:  docker-compose exec swissknife bash
echo.
echo Press Ctrl+C to stop following logs
echo.

REM Follow logs
docker-compose logs -f
goto end

:logs
docker-compose logs -f
goto end

:stop
echo 🛑 Stopping all services...
docker-compose down
goto end

:status
echo 📊 Service Status:
docker-compose ps
echo.
echo 🌐 Access URLs:
echo   Frontend Dashboard: http://localhost:8650
echo   Backend API:        http://localhost:8601
echo   API Documentation:  http://localhost:8601/docs
goto end

:help
echo Usage: %0 [dev^|prod^|logs^|stop^|status^|help]
echo.
echo Commands:
echo   dev        - Start in development mode with hot reload
echo   prod       - Start in production mode
echo   logs       - Show and follow logs
echo   stop       - Stop all services
echo   status     - Show service status
echo   help       - Show this help message
goto end

:end
pause
