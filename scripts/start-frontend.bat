@echo off
REM SwissKnife AI Scraper - Frontend Startup Script
REM This script starts the React development server

echo 🚀 Starting SwissKnife AI Scraper Frontend...

REM Check if we're in the right directory
if not exist "frontend\package.json" (
    echo ❌ Error: frontend\package.json not found. Please run this script from the project root.
    pause
    exit /b 1
)

REM Change to frontend directory
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    npm install
)

REM Check if .env exists
if not exist ".env" (
    echo ⚙️  Creating .env file from template...
    copy .env.example .env
)

REM Start the development server
echo 🌐 Starting React development server...
echo 📍 Frontend will be available at: http://localhost:8650
echo 🔗 Backend API should be running at: http://localhost:8601
echo.
echo Press Ctrl+C to stop the server

npm start
