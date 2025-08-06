# SwissKnife AI Scraper - Troubleshooting Guide

## 🔧 **Common Issues & Solutions**

This guide provides solutions to common problems encountered when setting up, developing, or deploying the SwissKnife AI Scraper.

---

## 🚨 **Critical Issues**

### **Services Not Starting**

#### **Problem**: Docker containers fail to start
```bash
# Error messages
ERROR: Port 8650 is already in use
ERROR: Cannot connect to the Docker daemon
ERROR: Service 'swissknife' failed to build
```

**Solutions:**
```bash
# Check port usage
netstat -an | findstr :8650
netstat -an | findstr :8601

# Kill processes using ports
# Windows
netstat -ano | findstr :8650
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8650 | xargs kill -9

# Restart Docker
# Windows/Mac: Restart Docker Desktop
# Linux
sudo systemctl restart docker

# Clean Docker system
docker system prune -a
docker volume prune
```

#### **Problem**: Database connection failures
```bash
# Error messages
FATAL: password authentication failed for user "postgres"
FATAL: database "swissknife" does not exist
could not connect to server: Connection refused
```

**Solutions:**
```bash
# Check PostgreSQL container
docker-compose logs postgres

# Reset database
docker-compose down postgres
docker volume rm scrapeagent_postgres_data
docker-compose up -d postgres

# Wait for database to be ready
docker-compose exec postgres pg_isready -U postgres

# Create database manually
docker-compose exec postgres createdb -U postgres swissknife

# Run migrations
docker-compose exec swissknife alembic upgrade head
```

### **Authentication System Issues**

#### **Problem**: JWT token errors
```bash
# Error messages
"Invalid token signature"
"Token has expired"
"Authentication required"
```

**Solutions:**
```python
# Check SECRET_KEY configuration
# Ensure SECRET_KEY is consistent across restarts
# Update .env file
SECRET_KEY=your-consistent-secret-key-here

# Clear browser storage
localStorage.clear()
sessionStorage.clear()

# Restart backend service
docker-compose restart swissknife
```

#### **Problem**: User registration/login failures
```bash
# Error messages
"Email already registered"
"Invalid email or password"
"Validation error"
```

**Solutions:**
```bash
# Check user database
docker-compose exec postgres psql -U postgres -d swissknife -c "SELECT * FROM users;"

# Reset user password
docker-compose exec swissknife python scripts/reset_password.py user@example.com

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

---

## 🌐 **Frontend Issues**

### **React Application Problems**

#### **Problem**: Frontend not loading
```bash
# Error messages
"Cannot GET /"
"This site can't be reached"
"ERR_CONNECTION_REFUSED"
```

**Solutions:**
```bash
# Check frontend container
docker-compose logs frontend

# Verify port mapping
docker-compose ps frontend

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend

# Check nginx configuration
docker-compose exec frontend cat /etc/nginx/nginx.conf

# Test direct access
curl http://localhost:8650
```

#### **Problem**: API calls failing from frontend
```bash
# Error messages
"Network Error"
"CORS policy error"
"Failed to fetch"
```

**Solutions:**
```typescript
// Check API client configuration
const API_BASE_URL = 'http://localhost:8601' // Correct port

// Verify CORS settings in backend
// config/settings.py
CORS_ORIGINS = [
    "http://localhost:8650",  # Frontend URL
    "http://frontend:80"      # Container URL
]

// Check network connectivity
curl -X POST http://localhost:8601/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### **Build Issues**

#### **Problem**: Frontend build failures
```bash
# Error messages
"Module not found"
"TypeScript compilation errors"
"Out of memory"
```

**Solutions:**
```bash
# Clear npm cache
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Increase memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build

# Fix TypeScript errors
npm run type-check
# Address type errors in code

# Check dependencies
npm audit fix
npm update
```

---

## 🔧 **Backend Issues**

### **FastAPI Application Problems**

#### **Problem**: Backend API not responding
```bash
# Error messages
"Internal Server Error"
"Service Unavailable"
"Connection timeout"
```

**Solutions:**
```bash
# Check backend logs
docker-compose logs -f swissknife

# Verify health endpoint
curl http://localhost:8601/health

# Check dependencies
docker-compose exec swissknife python -c "import crawl4ai; print('OK')"

# Restart with debug mode
docker-compose exec swissknife python main.py --debug

# Check resource usage
docker stats swissknife
```

#### **Problem**: Import errors
```bash
# Error messages
"ModuleNotFoundError: No module named 'crawl4ai'"
"ImportError: cannot import name 'SwissKnifeScraper'"
```

**Solutions:**
```bash
# Check Python path
docker-compose exec swissknife python -c "import sys; print(sys.path)"

# Install missing dependencies
docker-compose exec swissknife pip install -r requirements.txt

# Rebuild container
docker-compose build --no-cache swissknife

# Check file permissions
docker-compose exec swissknife ls -la /app
```

### **Database Issues**

#### **Problem**: Migration failures
```bash
# Error messages
"Target database is not up to date"
"Migration failed"
"Duplicate column name"
```

**Solutions:**
```bash
# Check migration status
docker-compose exec swissknife alembic current
docker-compose exec swissknife alembic history

# Reset migrations (CAUTION: Data loss)
docker-compose exec swissknife alembic downgrade base
docker-compose exec swissknife alembic upgrade head

# Manual migration
docker-compose exec postgres psql -U postgres -d swissknife
# Run SQL commands manually

# Check database schema
docker-compose exec postgres psql -U postgres -d swissknife -c "\dt"
```

---

## 🕷️ **Scraping Issues**

### **Crawl4AI Problems**

#### **Problem**: Crawl4AI service not responding
```bash
# Error messages
"Connection refused to crawl4ai:11235"
"Crawl4AI service unavailable"
"Timeout waiting for response"
```

**Solutions:**
```bash
# Check Crawl4AI container
docker-compose logs crawl4ai

# Verify service health
curl http://localhost:11235/health

# Restart Crawl4AI service
docker-compose restart crawl4ai

# Check resource limits
docker stats swissknife-crawl4ai

# Update Crawl4AI image
docker-compose pull crawl4ai
docker-compose up -d crawl4ai
```

#### **Problem**: Scraping failures
```bash
# Error messages
"Failed to extract content"
"Timeout during scraping"
"Invalid URL format"
```

**Solutions:**
```python
# Test scraping directly
import asyncio
from core.scraper import SwissKnifeScraper

async def test_scrape():
    async with SwissKnifeScraper() as scraper:
        await scraper.initialize()
        result = await scraper.scrape("https://httpbin.org/html")
        print(result)

asyncio.run(test_scrape())

# Check URL accessibility
curl -I https://example.com

# Verify proxy settings
# Check proxy_manager.py configuration

# Test with different extraction strategies
result = await scraper.scrape(url, {
    "extraction_strategy": "NoExtractionStrategy"
})
```

### **AI Integration Issues**

#### **Problem**: Jina AI API failures
```bash
# Error messages
"Invalid API key"
"Rate limit exceeded"
"Jina AI service unavailable"
```

**Solutions:**
```bash
# Verify API key
echo $JINA_AI_API_KEY

# Test API directly
curl -X POST "https://r.jina.ai/" \
  -H "Authorization: Bearer $JINA_AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Check rate limits
# Review Jina AI dashboard for usage

# Use fallback extraction
# Modify scraper to handle API failures gracefully
```

#### **Problem**: Ollama LLM issues
```bash
# Error messages
"Ollama service not available"
"Model not found"
"Out of memory"
```

**Solutions:**
```bash
# Check Ollama container
docker-compose logs ollama

# List available models
docker-compose exec ollama ollama list

# Pull required model
docker-compose exec ollama ollama pull llama2

# Increase memory limits
# Update docker-compose.yml
deploy:
  resources:
    limits:
      memory: 8G
```

---

## 🔒 **Security Issues**

### **Authentication Problems**

#### **Problem**: CORS errors
```bash
# Error messages
"Access to fetch blocked by CORS policy"
"Cross-Origin Request Blocked"
```

**Solutions:**
```python
# Update CORS configuration
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8650",
        "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# For development only
allow_origins=["*"]  # NEVER use in production
```

#### **Problem**: SSL/TLS certificate issues
```bash
# Error messages
"SSL certificate verify failed"
"Certificate has expired"
"Hostname doesn't match certificate"
```

**Solutions:**
```bash
# Check certificate validity
openssl x509 -in certificate.crt -text -noout

# Renew Let's Encrypt certificate
certbot renew --nginx

# Update nginx configuration
# Verify SSL configuration
nginx -t

# Test SSL
curl -I https://yourdomain.com
```

---

## 📊 **Performance Issues**

### **Slow Response Times**

#### **Problem**: API responses are slow
```bash
# Symptoms
Response times > 5 seconds
High CPU usage
Memory leaks
```

**Solutions:**
```bash
# Check system resources
docker stats

# Profile application
docker-compose exec swissknife python -m cProfile -o profile.stats main.py

# Optimize database queries
# Add indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

# Enable Redis caching
# Check cache hit rates
docker-compose exec redis redis-cli info stats

# Scale horizontally
# Add more backend instances
docker-compose up -d --scale swissknife=3
```

### **Memory Issues**

#### **Problem**: Out of memory errors
```bash
# Error messages
"MemoryError"
"Container killed (OOMKilled)"
"Cannot allocate memory"
```

**Solutions:**
```bash
# Increase container memory limits
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G

# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Optimize code for memory usage
# Use generators instead of lists
# Clear large objects after use
# Implement proper garbage collection
```

---

## 🔍 **Debugging Tools**

### **Log Analysis**

#### **Centralized Logging**
```bash
# View all logs
docker-compose logs -f

# Filter by service
docker-compose logs -f swissknife
docker-compose logs -f frontend
docker-compose logs -f crawl4ai

# Search logs
docker-compose logs swissknife | grep ERROR
docker-compose logs swissknife | grep "scraping failed"

# Export logs
docker-compose logs swissknife > debug.log
```

#### **Structured Logging**
```python
# Add detailed logging
import structlog

logger = structlog.get_logger(__name__)

async def scrape_url(url: str):
    logger.info("Starting scrape", url=url, timestamp=datetime.now())
    try:
        result = await perform_scrape(url)
        logger.info("Scrape successful", 
                   url=url, 
                   items_found=len(result),
                   duration=time.time() - start_time)
        return result
    except Exception as e:
        logger.error("Scrape failed", 
                    url=url, 
                    error=str(e), 
                    exc_info=True)
        raise
```

### **Health Monitoring**

#### **Health Check Endpoints**
```bash
# Basic health check
curl http://localhost:8601/health

# Detailed health check
curl http://localhost:8601/health/detailed

# Service-specific checks
curl http://localhost:11235/health  # Crawl4AI
curl http://localhost:6379/ping     # Redis
```

#### **Performance Monitoring**
```bash
# Monitor API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8601/health

# curl-format.txt content:
#      time_namelookup:  %{time_namelookup}\n
#         time_connect:  %{time_connect}\n
#      time_appconnect:  %{time_appconnect}\n
#     time_pretransfer:  %{time_pretransfer}\n
#        time_redirect:  %{time_redirect}\n
#   time_starttransfer:  %{time_starttransfer}\n
#                      ----------\n
#           time_total:  %{time_total}\n
```

---

## 🛠️ **Development Issues**

### **IDE and Development Tools**

#### **Problem**: VS Code not recognizing imports
```bash
# Solutions
# Install Python extension
# Set Python interpreter path
# Update settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true
}

# Reload VS Code window
Ctrl+Shift+P -> "Developer: Reload Window"
```

#### **Problem**: Hot reload not working
```bash
# Frontend hot reload
# Check if files are being watched
# Update package.json
"scripts": {
    "start": "react-scripts start",
    "dev": "CHOKIDAR_USEPOLLING=true react-scripts start"
}

# Backend hot reload
# Ensure uvicorn is running with --reload
uvicorn main:app --reload --host 0.0.0.0 --port 8601
```

### **Testing Issues**

#### **Problem**: Tests failing
```bash
# Run tests with verbose output
pytest -v --tb=short

# Run specific test
pytest tests/test_scraper.py::TestSwissKnifeScraper::test_basic_scraping -v

# Debug test failures
pytest --pdb tests/test_scraper.py

# Check test coverage
pytest --cov=. --cov-report=html
```

---

## 📞 **Getting Help**

### **Self-Diagnosis Checklist**
1. **Check service status**: `docker-compose ps`
2. **Review logs**: `docker-compose logs -f service-name`
3. **Verify ports**: `netstat -an | findstr :8650`
4. **Test connectivity**: `curl http://localhost:8601/health`
5. **Check resources**: `docker stats`
6. **Verify configuration**: Review `.env` file
7. **Test authentication**: Try login/register flow
8. **Check external services**: Jina AI, Crawl4AI status

### **Diagnostic Commands**
```bash
# Complete system check
#!/bin/bash
echo "=== SwissKnife AI Scraper Diagnostic ==="
echo "Date: $(date)"
echo ""

echo "=== Docker Status ==="
docker --version
docker-compose --version
docker-compose ps

echo "=== Port Status ==="
netstat -an | grep -E ":(8650|8601|11235|5434|6379|11435)"

echo "=== Service Health ==="
curl -s http://localhost:8601/health || echo "Backend: FAILED"
curl -s http://localhost:8650 || echo "Frontend: FAILED"
curl -s http://localhost:11235/health || echo "Crawl4AI: FAILED"

echo "=== Resource Usage ==="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo "=== Recent Errors ==="
docker-compose logs --tail=10 swissknife | grep -i error
```

### **Support Resources**
- **Documentation**: Check other files in Help/ directory
- **API Reference**: http://localhost:8601/docs
- **Health Status**: http://localhost:8601/health/detailed
- **GitHub Issues**: Create issue with diagnostic output
- **Community**: Check project discussions and forums

### **Creating Bug Reports**
When reporting issues, include:
1. **Environment details**: OS, Docker version, browser
2. **Steps to reproduce**: Exact sequence of actions
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Error messages**: Complete error logs
6. **Diagnostic output**: Run diagnostic script above
7. **Configuration**: Relevant parts of .env and docker-compose.yml

---

## 🎯 **Prevention Tips**

### **Best Practices**
1. **Regular updates**: Keep Docker images and dependencies updated
2. **Monitor resources**: Set up alerts for high CPU/memory usage
3. **Backup regularly**: Automated database and volume backups
4. **Test thoroughly**: Run full test suite before deployment
5. **Monitor logs**: Set up log aggregation and alerting
6. **Document changes**: Keep track of configuration changes
7. **Use staging**: Test changes in staging environment first

### **Maintenance Schedule**
- **Daily**: Check service health and error logs
- **Weekly**: Review performance metrics and resource usage
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Full system backup and disaster recovery test

---

**This troubleshooting guide covers the most common issues. For complex problems, use the diagnostic tools and create detailed bug reports for further assistance.**

---

**Last Updated**: August 6, 2025  
**Version**: 2.2.0