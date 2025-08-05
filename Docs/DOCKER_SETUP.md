# SwissKnife AI Scraper - Docker Setup Guide

Complete containerization setup for the SwissKnife AI Scraper full-stack application.

## 🐳 Overview

The SwissKnife AI Scraper provides a complete Docker containerization setup with:

- **Backend Container**: FastAPI application with all dependencies
- **Frontend Container**: React dashboard with nginx
- **Multi-Service Orchestration**: Docker Compose for all services
- **Development & Production**: Separate configurations for different environments
- **One-Command Launch**: Simple commands to run the entire platform

## 📋 Prerequisites

- **Docker**: Version 20.10+ 
- **Docker Compose**: Version 2.0+
- **System Requirements**: 4GB RAM minimum, 8GB recommended

### Installation

**Windows:**
- Download Docker Desktop from [docker.com](https://docker.com)
- Enable WSL2 integration

**macOS:**
- Download Docker Desktop from [docker.com](https://docker.com)
- Install and start Docker Desktop

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🚀 Quick Start

### One-Command Launch

**Using Make (Recommended):**
```bash
# Launch full-stack application
make docker-launch

# Or specific environments
make docker-dev    # Development with hot reload
make docker-prod   # Production optimized
```

**Using Scripts Directly:**
```bash
# Windows
scripts\docker-launch.bat

# Linux/macOS
bash scripts/docker-launch.sh
```

**Using Docker Compose:**
```bash
# Default environment
docker-compose up --build -d

# Development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# Production environment
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🌐 Access URLs

After launching, access the application at:

- **Frontend Dashboard**: http://localhost:8650
- **Backend API**: http://localhost:8601
- **API Documentation**: http://localhost:8601/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Ollama**: http://localhost:11434

## 🏗️ Architecture

### Container Structure

```
SwissKnife AI Scraper Docker Setup
├── Backend Container (swissknife)
│   ├── FastAPI application
│   ├── Python 3.11 runtime
│   ├── All dependencies from requirements.txt
│   ├── Playwright browsers
│   └── Port 8601
├── Frontend Container (frontend)
│   ├── React application
│   ├── Nginx web server
│   ├── Built static files
│   └── Port 8650 (mapped from 80)
├── PostgreSQL Container
│   ├── Database storage
│   └── Port 5432
├── Redis Container
│   ├── Caching and sessions
│   └── Port 6379
└── Ollama Container
    ├── Local LLM processing
    └── Port 11434
```

### Network Configuration

All containers communicate through a custom Docker network (`swissknife-network`) with:
- **Internal DNS**: Containers can reach each other by service name
- **Port Mapping**: External access through mapped ports
- **Health Checks**: Automatic service health monitoring
- **Dependency Management**: Proper startup order

## 🔧 Configuration Files

### Main Files

- **`Dockerfile`**: Backend container definition with multi-stage builds
- **`frontend/Dockerfile`**: Frontend production container
- **`frontend/Dockerfile.dev`**: Frontend development container
- **`docker-compose.yml`**: Main orchestration file
- **`docker-compose.dev.yml`**: Development overrides
- **`docker-compose.prod.yml`**: Production configuration

### Environment Variables

**Backend (.env):**
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8601
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/swissknife

# Redis
REDIS_URL=redis://redis:6379

# Ollama
OLLAMA_ENDPOINT=http://ollama:11434
```

**Frontend (frontend/.env):**
```bash
# API URL
REACT_APP_API_URL=http://localhost:8601

# Environment
REACT_APP_ENV=development
PORT=8650
```

## 🛠️ Development Mode

Development mode provides:
- **Hot Reload**: Automatic restart on code changes
- **Source Mounting**: Live code editing
- **Debug Logging**: Detailed logs for development
- **Development Tools**: Additional debugging utilities

```bash
# Start development environment
make docker-dev

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

### Development Features

- **Backend**: Uvicorn with `--reload` flag
- **Frontend**: React development server with hot reload
- **Volume Mounting**: Source code mounted for live editing
- **Debug Mode**: Enhanced logging and error reporting

## 🏭 Production Mode

Production mode provides:
- **Optimized Performance**: Gunicorn with multiple workers
- **Security**: Production security settings
- **Resource Limits**: Memory and CPU constraints
- **Health Monitoring**: Comprehensive health checks

```bash
# Start production environment
make docker-prod

# Or manually
docker-compose -f docker-compose.prod.yml up --build -d
```

### Production Features

- **Backend**: Gunicorn with 4 workers
- **Frontend**: Optimized React build with nginx
- **No Source Mounting**: Only built artifacts
- **Resource Management**: CPU and memory limits

## 📊 Management Commands

### Using Make

```bash
# Build containers
make docker-build

# Start services
make docker-up

# Stop services
make docker-down

# View logs
make docker-logs

# Check status
make docker-status

# Clean up
make docker-clean
```

### Using Docker Compose

```bash
# View running services
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Restart service
docker-compose restart [service_name]

# Scale service
docker-compose up -d --scale swissknife=2

# Execute commands in container
docker-compose exec swissknife bash
docker-compose exec frontend sh

# Stop and remove everything
docker-compose down -v
```

## 🔍 Troubleshooting

### Common Issues

**Port Conflicts:**
```bash
# Check what's using ports
netstat -tulpn | grep :8650
netstat -tulpn | grep :8601

# Kill processes on ports
sudo lsof -ti:8650 | xargs kill -9
sudo lsof -ti:8601 | xargs kill -9
```

**Container Health Issues:**
```bash
# Check container health
docker-compose ps

# View detailed logs
docker-compose logs swissknife
docker-compose logs frontend

# Restart unhealthy services
docker-compose restart swissknife
```

**Build Issues:**
```bash
# Clean build (no cache)
docker-compose build --no-cache

# Remove all containers and rebuild
docker-compose down -v
docker system prune -f
make docker-build
```

### Health Checks

All services include health checks:
- **Backend**: HTTP check on `/health` endpoint
- **Frontend**: HTTP check on nginx
- **PostgreSQL**: `pg_isready` check
- **Redis**: `redis-cli ping` check
- **Ollama**: API tags endpoint check

## 📈 Performance Optimization

### Resource Allocation

**Development:**
- No resource limits for easier debugging
- Full source code mounting

**Production:**
- Backend: 2GB RAM limit, 1 CPU
- Frontend: 512MB RAM limit, 0.5 CPU
- Database: Optimized for workload

### Scaling

```bash
# Scale backend horizontally
docker-compose up -d --scale swissknife=3

# Use load balancer (nginx)
docker-compose --profile reverse-proxy up -d
```

## 🔒 Security

### Production Security

- **Non-root users**: All containers run as non-root
- **Network isolation**: Custom Docker network
- **Environment variables**: Sensitive data in env files
- **Health monitoring**: Automatic restart on failures

### Best Practices

- Keep Docker images updated
- Use specific image tags (not `latest`)
- Regularly update dependencies
- Monitor container logs
- Use secrets management for production

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [React Docker Guide](https://create-react-app.dev/docs/deployment/#docker)

---

This Docker setup provides a complete, production-ready containerization solution for the SwissKnife AI Scraper platform.
