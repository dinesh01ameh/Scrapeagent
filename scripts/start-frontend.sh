#!/bin/bash

# SwissKnife AI Scraper - Frontend Startup Script
# This script starts the React development server

set -e

echo "🚀 Starting SwissKnife AI Scraper Frontend..."

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: frontend/package.json not found. Please run this script from the project root."
    exit 1
fi

# Change to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
fi

# Start the development server
echo "🌐 Starting React development server..."
echo "📍 Frontend will be available at: http://localhost:8650"
echo "🔗 Backend API should be running at: http://localhost:8601"
echo ""
echo "Press Ctrl+C to stop the server"

npm start
