# SwissKnife AI Scraper Makefile

.PHONY: help install dev start test clean docker-build docker-up docker-down docker-dev docker-prod docker-launch docker-logs docker-status docker-clean lint format install-frontend frontend build-frontend fullstack

# Default target
help:
	@echo "SwissKnife AI Scraper - Available Commands:"
	@echo "=========================================="
	@echo "install      - Install dependencies"
	@echo "dev          - Install development dependencies"
	@echo "start        - Start the application on port 8601"
	@echo "start-dev    - Start in development mode"
	@echo "restart-clean - Clean restart (kill old processes)"
	@echo "test         - Run tests"
	@echo "lint         - Run linting"
	@echo "format       - Format code"
	@echo "clean        - Clean cache and temporary files"
	@echo "check-port   - Check port 8601 status"
	@echo "kill-port    - Kill processes on port 8601"
	@echo "docker-build - Build Docker images"
	@echo "docker-up    - Start with Docker Compose"
	@echo "docker-down  - Stop Docker Compose"
	@echo "docker-dev   - Start development environment"
	@echo "docker-prod  - Start production environment"
	@echo "docker-logs  - View Docker logs"
	@echo "docker-launch - Full Docker launch (interactive)"
	@echo "setup-ollama - Setup Ollama with default models"
	@echo "check        - Check system requirements and port"
	@echo ""
	@echo "Frontend:"
	@echo "frontend     - Start frontend development server"
	@echo "install-frontend - Install frontend dependencies"
	@echo "build-frontend - Build frontend for production"
	@echo "fullstack    - Start both backend and frontend"

# Installation
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	playwright install chromium

dev: install
	@echo "🔧 Installing development dependencies..."
	pip install -e ".[dev]"
	pre-commit install

# Running
start:
	@echo "🚀 Starting SwissKnife AI Scraper..."
	python scripts/start.py

start-dev:
	@echo "🔧 Starting in development mode..."
	uvicorn main:app --reload --host 0.0.0.0 --port 8601

# Testing
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Code quality
lint:
	@echo "🔍 Running linting..."
	flake8 .
	mypy .

format:
	@echo "✨ Formatting code..."
	black .
	isort .

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

# Docker Commands
docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build

docker-up:
	@echo "🐳 Starting with Docker Compose..."
	docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker Compose..."
	docker-compose down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

docker-dev:
	@echo "🐳 Starting development environment..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

docker-prod:
	@echo "🐳 Starting production environment..."
	docker-compose -f docker-compose.prod.yml up --build -d

docker-launch:
	@echo "🚀 Launching full-stack Docker environment..."
	@if exist "scripts\docker-launch.bat" (scripts\docker-launch.bat) else (bash scripts/docker-launch.sh)

docker-status:
	@echo "📊 Docker service status..."
	docker-compose ps

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f

# Ollama setup
setup-ollama:
	@echo "🤖 Setting up Ollama..."
	@echo "Installing default models..."
	ollama pull mistral
	ollama pull llama3.2
	@echo "✅ Ollama setup complete!"

# Database
db-init:
	@echo "🗄️ Initializing database..."
	# Add database initialization commands here

# Environment
env-setup:
	@echo "⚙️ Setting up environment..."
	cp .env.example .env
	@echo "✅ Environment file created. Please edit .env with your settings."

# Full setup for new installations
setup: env-setup install setup-ollama
	@echo "🎉 Setup complete!"
	@echo "Edit .env file with your configuration, then run 'make start'"

# Production deployment
deploy:
	@echo "🚀 Deploying to production..."
	# Add deployment commands here

# Monitoring
logs:
	@echo "📋 Showing application logs..."
	tail -f logs/swissknife.log

# Development helpers
shell:
	@echo "🐚 Starting Python shell with app context..."
	python -c "from main import app; import IPython; IPython.embed()"

# Port management
check-port:
	@echo "🔌 Checking port 8601 status..."
	@python -c "from utils.port_manager import get_port_info; import json; print(json.dumps(get_port_info(), indent=2))"

kill-port:
	@echo "🔪 Killing processes on port 8601..."
	@python -c "from utils.port_manager import PortManager; pm = PortManager(); pm.kill_process_on_port(8601, force=True)"

restart-clean:
	@echo "🔄 Clean restart - killing old processes and restarting..."
	@python -c "from utils.port_manager import check_and_prepare_port; check_and_prepare_port()"
	@$(MAKE) start

# Check system requirements
check:
	@echo "🔍 Checking system requirements..."
	@python -c "import sys; print(f'Python: {sys.version}')"
	@docker --version 2>/dev/null || echo "Docker: Not installed"
	@ollama --version 2>/dev/null || echo "Ollama: Not installed"
	@$(MAKE) check-port

# Frontend commands
install-frontend:
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && npm install

frontend:
	@echo "🌐 Starting frontend development server..."
	@if exist "scripts\start-frontend.bat" (scripts\start-frontend.bat) else (bash scripts/start-frontend.sh)

build-frontend:
	@echo "🏗️ Building frontend for production..."
	@cd frontend && npm run build

fullstack:
	@echo "🚀 Starting full-stack development environment..."
	@echo "Starting backend on port 8601..."
	@start /B python -m uvicorn main:app --host 0.0.0.0 --port 8601 --reload
	@timeout /t 3 /nobreak > nul
	@echo "Starting frontend on port 8650..."
	@cd frontend && start npm start
