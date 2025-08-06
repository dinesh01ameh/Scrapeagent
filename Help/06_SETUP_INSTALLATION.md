# SwissKnife AI Scraper - Setup & Installation Guide

## 🚀 **Complete Project Setup**

This guide provides step-by-step instructions for setting up the SwissKnife AI Scraper project from scratch. Follow these instructions to get a fully functional development environment.

---

## 📋 **Prerequisites**

### **Required Software**
1. **Docker & Docker Compose**
   - Docker Desktop 4.0+ (Windows/Mac) or Docker Engine 20.0+ (Linux)
   - Docker Compose 2.0+
   - Minimum 8GB RAM, 20GB free disk space

2. **Git**
   - Git 2.30+ for version control
   - GitHub account for repository access

3. **Node.js & npm** (for frontend development)
   - Node.js 18.0+ LTS
   - npm 9.0+ or yarn 1.22+

4. **Python** (for backend development)
   - Python 3.11+
   - pip 23.0+

### **System Requirements**
- **Operating System**: Windows 10+, macOS 12+, or Linux (Ubuntu 20.04+)
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 20GB free disk space
- **Network**: Stable internet connection for Docker images and API services

---

## 📥 **Installation Steps**

### **Step 1: Clone the Repository**
```bash
# Clone the repository
git clone https://github.com/your-username/SwissKnife-AI-Scraper.git
cd SwissKnife-AI-Scraper

# Verify repository structure
ls -la
```

**Expected structure:**
```
SwissKnife-AI-Scraper/
├── api/                    # Backend API routes
├── core/                   # Core scraping engine
├── services/               # External service integrations
├── frontend/               # React frontend
├── config/                 # Configuration files
├── docker-compose.yml      # Docker services
├── Dockerfile             # Backend container
├── requirements.txt       # Python dependencies
├── main.py               # Application entry point
└── Help/                 # This documentation
```

### **Step 2: Environment Configuration**
```bash
# Create environment file
cp .env.example .env

# Edit environment variables
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# Core Application
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=true
ENVIRONMENT=development

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5434/swissknife
REDIS_URL=redis://localhost:6379

# External API Keys
JINA_AI_API_KEY=your-jina-ai-api-key
OPENAI_API_KEY=your-openai-api-key-optional
ANTHROPIC_API_KEY=your-anthropic-api-key-optional
GROQ_API_KEY=your-groq-api-key-optional

# Service URLs
CRAWL4AI_BASE_URL=http://localhost:11235
OLLAMA_ENDPOINT=http://localhost:11435

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8601
REACT_APP_ENV=development
```

### **Step 3: Docker Services Setup**
```bash
# Pull required Docker images
docker-compose pull

# Build custom images
docker-compose build

# Start all services
docker-compose up -d

# Verify all services are running
docker-compose ps
```

**Expected output:**
```
NAME                     COMMAND                  SERVICE             STATUS              PORTS
scrapeagent-frontend-1   "nginx -g 'daemon of…"   frontend            running (healthy)   0.0.0.0:8650->80/tcp
scrapeagent-swissknife-1 "uvicorn main:app --…"   swissknife          running (healthy)   0.0.0.0:8601->8601/tcp
swissknife-crawl4ai      "python -m crawl4ai.…"   crawl4ai            running (healthy)   0.0.0.0:11235->11235/tcp
scrapeagent-postgres-1   "docker-entrypoint.s…"   postgres            running             0.0.0.0:5434->5432/tcp
scrapeagent-redis-1      "docker-entrypoint.s…"   redis               running             0.0.0.0:6379->6379/tcp
scrapeagent-ollama-1     "/bin/ollama serve"      ollama              running             0.0.0.0:11435->11434/tcp
```

### **Step 4: Database Initialization**
```bash
# Run database migrations
docker-compose exec swissknife python -m alembic upgrade head

# Create initial admin user (optional)
docker-compose exec swissknife python scripts/create_admin.py
```

### **Step 5: Service Health Verification**
```bash
# Check backend health
curl http://localhost:8601/health

# Check frontend accessibility
curl http://localhost:8650

# Check Crawl4AI service
curl http://localhost:11235/health

# Check detailed system health
curl http://localhost:8601/health/detailed
```

**Expected health response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-06T12:00:00Z",
  "version": "2.2.0",
  "services": {
    "database": {"status": "healthy", "response_time": 12},
    "redis": {"status": "healthy", "response_time": 3},
    "crawl4ai": {"status": "healthy", "response_time": 45}
  }
}
```

---

## 🔧 **Development Setup**

### **Backend Development**
```bash
# Install Python dependencies locally (optional for IDE support)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run backend in development mode
docker-compose up -d postgres redis crawl4ai ollama
python main.py

# Or use Docker with hot reload
docker-compose up -d swissknife
```

### **Frontend Development**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Or use Docker
docker-compose up -d frontend
```

### **Development URLs**
- **Frontend**: http://localhost:8650
- **Backend API**: http://localhost:8601
- **API Documentation**: http://localhost:8601/docs
- **Database**: localhost:5434
- **Redis**: localhost:6379

---

## 🧪 **Testing Setup**

### **Backend Testing**
```bash
# Run all tests
docker-compose exec swissknife pytest

# Run with coverage
docker-compose exec swissknife pytest --cov=. --cov-report=html

# Run specific test file
docker-compose exec swissknife pytest tests/test_scraper.py -v
```

### **Frontend Testing**
```bash
# Navigate to frontend directory
cd frontend

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run end-to-end tests
npm run test:e2e
```

### **Integration Testing**
```bash
# Run full integration tests
docker-compose exec swissknife pytest tests/integration/ -v

# Test authentication flow
docker-compose exec swissknife pytest tests/integration/test_auth_flow.py -v
```

---

## 🔒 **Security Configuration**

### **Production Security Settings**
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file with production values
SECRET_KEY=your-generated-secure-key
DEBUG=false
ENVIRONMENT=production

# Configure CORS for production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### **SSL/TLS Configuration**
```bash
# For production deployment, configure SSL certificates
# Update docker-compose.yml with SSL settings
# Add nginx SSL configuration
```

---

## 📊 **Monitoring Setup**

### **Enable Monitoring Services**
```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access monitoring dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

### **Log Configuration**
```bash
# View application logs
docker-compose logs -f swissknife

# View specific service logs
docker-compose logs -f crawl4ai
docker-compose logs -f frontend

# Export logs for analysis
docker-compose logs swissknife > swissknife.log
```

---

## 🚨 **Troubleshooting**

### **Common Issues & Solutions**

#### **Port Conflicts**
```bash
# Check what's using the ports
netstat -an | findstr :8650
netstat -an | findstr :8601

# Stop conflicting services
# Update docker-compose.yml ports if needed
```

#### **Docker Issues**
```bash
# Clean Docker system
docker system prune -a

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Reset database
docker-compose down postgres
docker volume rm scrapeagent_postgres_data
docker-compose up -d postgres
```

#### **Frontend Build Issues**
```bash
# Clear npm cache
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Rebuild frontend container
docker-compose build --no-cache frontend
```

#### **Service Health Check Failures**
```bash
# Check service logs
docker-compose logs service-name

# Restart specific service
docker-compose restart service-name

# Check service dependencies
docker-compose exec swissknife curl http://crawl4ai:11235/health
```

---

## 🔄 **Update & Maintenance**

### **Updating the Application**
```bash
# Pull latest changes
git pull origin main

# Update Docker images
docker-compose pull

# Rebuild and restart services
docker-compose down
docker-compose build
docker-compose up -d

# Run database migrations
docker-compose exec swissknife python -m alembic upgrade head
```

### **Backup & Restore**
```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres swissknife > backup.sql

# Backup volumes
docker run --rm -v scrapeagent_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore database
docker-compose exec -T postgres psql -U postgres swissknife < backup.sql
```

---

## 📱 **Mobile Development Setup**

### **React Native Setup** (if applicable)
```bash
# Install React Native CLI
npm install -g @react-native-community/cli

# Create mobile app
npx react-native init SwissKnifeMobile

# Configure API endpoints
# Update mobile app configuration
```

---

## 🌐 **Production Deployment**

### **Docker Production Setup**
```bash
# Create production docker-compose file
cp docker-compose.yml docker-compose.prod.yml

# Update production configuration
# - Remove development volumes
# - Add SSL certificates
# - Configure production databases
# - Set production environment variables

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### **Cloud Deployment Options**
- **AWS**: ECS, EKS, or EC2 with Docker
- **Google Cloud**: Cloud Run, GKE, or Compute Engine
- **Azure**: Container Instances, AKS, or Virtual Machines
- **DigitalOcean**: App Platform or Droplets
- **Heroku**: Container deployment

---

## ✅ **Verification Checklist**

After setup, verify the following:

### **Services Running**
- [ ] Frontend accessible at http://localhost:8650
- [ ] Backend API responding at http://localhost:8601
- [ ] API documentation available at http://localhost:8601/docs
- [ ] Database connection working
- [ ] Redis cache operational
- [ ] Crawl4AI service healthy
- [ ] Ollama LLM service running

### **Authentication System**
- [ ] User registration working
- [ ] User login functional
- [ ] JWT token generation and validation
- [ ] Protected routes enforced
- [ ] Session persistence working

### **Scraping Functionality**
- [ ] Basic scraping endpoint working
- [ ] Natural language scraping functional
- [ ] Multimodal processing operational
- [ ] Job scheduling working
- [ ] Results storage and retrieval

### **Performance & Monitoring**
- [ ] Health checks passing
- [ ] Logging configured and working
- [ ] Caching operational
- [ ] Performance metrics available
- [ ] Error handling working correctly

---

## 📞 **Support & Resources**

### **Getting Help**
- **Documentation**: Check other files in the Help/ directory
- **API Reference**: http://localhost:8601/docs
- **Health Status**: http://localhost:8601/health/detailed
- **Logs**: `docker-compose logs -f service-name`

### **Development Resources**
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **Docker Documentation**: https://docs.docker.com/
- **Crawl4AI Documentation**: https://crawl4ai.com/docs

---

**Congratulations! Your SwissKnife AI Scraper is now ready for development and testing.**

**Next Steps:**
1. **Explore Features**: See [05_FEATURE_DOCUMENTATION.md](./05_FEATURE_DOCUMENTATION.md)
2. **Development Guide**: See [07_DEVELOPMENT_GUIDE.md](./07_DEVELOPMENT_GUIDE.md)
3. **API Usage**: See [03_API_REFERENCE.md](./03_API_REFERENCE.md)

---

**Last Updated**: August 6, 2025  
**Version**: 2.2.0