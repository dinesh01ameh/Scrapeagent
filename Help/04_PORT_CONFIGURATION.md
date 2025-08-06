# SwissKnife AI Scraper - Port Configuration Guide

## 🌐 **OFFICIAL PORT MAPPING**

This document establishes the **PERMANENT** port configuration for the SwissKnife AI Scraper project. These ports are standardized and must be used consistently across all environments.

---

## 📋 **PRIMARY SERVICES**

### **Frontend Application**
- **Service**: React Dashboard (Smart Scraper AI)
- **Port**: `8650`
- **URL**: `http://localhost:8650`
- **Container**: `scrapeagent-frontend-1`
- **Technology**: React + Material-UI served via Nginx
- **Purpose**: Main user interface for the Smart Scraper AI platform

### **Backend API**
- **Service**: FastAPI Backend
- **Port**: `8601`
- **URL**: `http://localhost:8601`
- **Container**: `scrapeagent-swissknife-1`
- **Technology**: FastAPI with Python
- **Purpose**: Core API endpoints, authentication, and business logic

---

## 🔧 **CORE SERVICES**

### **Crawl4AI Scraping Engine**
- **Service**: Crawl4AI Docker Service
- **Port**: `11235`
- **URL**: `http://localhost:11235`
- **Container**: `swissknife-crawl4ai`
- **Technology**: Crawl4AI with Playwright
- **Purpose**: Primary web scraping and content extraction engine

### **PostgreSQL Database**
- **Service**: Primary Database
- **Port**: `5434`
- **URL**: `localhost:5434`
- **Container**: `scrapeagent-postgres-1`
- **Technology**: PostgreSQL 15
- **Purpose**: Primary data storage for users, projects, jobs, and content

### **Redis Cache**
- **Service**: Cache and Session Store
- **Port**: `6379`
- **URL**: `localhost:6379`
- **Container**: `scrapeagent-redis-1`
- **Technology**: Redis 7
- **Purpose**: Session management, caching, and temporary data storage

### **Ollama LLM**
- **Service**: Local AI Processing
- **Port**: `11435`
- **URL**: `http://localhost:11435`
- **Container**: `scrapeagent-ollama-1`
- **Technology**: Ollama
- **Purpose**: Local large language model processing

---

## 🚨 **CRITICAL RULES**

### **MANDATORY PORT USAGE**
1. **Frontend MUST be accessed via**: `http://localhost:8650`
2. **Backend API MUST be accessed via**: `http://localhost:8601`
3. **All browser automation tests MUST use port 8650**
4. **All API calls MUST target port 8601**
5. **DO NOT CHANGE THESE PORTS** without updating all documentation

### **Port Conflict Avoidance**
- **Port 3000**: Reserved for Open WebUI (separate application)
- **Port 8080**: Reserved for other services
- **Port 5432**: Reserved for Supabase PostgreSQL
- **Port 11434**: Reserved for main Ollama instance

---

## 🧪 **TESTING CONFIGURATION**

### **Browser Automation (Playwright)**
```javascript
// ✅ CORRECT - Use these URLs for testing
const FRONTEND_URL = 'http://localhost:8650';
const BACKEND_URL = 'http://localhost:8601';

// ❌ INCORRECT - Do not use these
const WRONG_URL = 'http://localhost:3000'; // This is Open WebUI
```

### **API Testing**
```bash
# ✅ CORRECT - Health check
curl http://localhost:8601/health

# ✅ CORRECT - Authentication
curl -X POST http://localhost:8601/auth/login

# ✅ CORRECT - Frontend access
curl http://localhost:8650
```

---

## 📊 **SERVICE VERIFICATION**

### **Check Running Services**
```bash
# Verify all containers are running on correct ports
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
```

### **Expected Output**
```
NAMES                     PORTS                           STATUS
scrapeagent-frontend-1    0.0.0.0:8650->80/tcp           Up (healthy)
scrapeagent-swissknife-1  0.0.0.0:8601->8601/tcp         Up (healthy)
swissknife-crawl4ai       0.0.0.0:11235->11235/tcp       Up (healthy)
scrapeagent-postgres-1    0.0.0.0:5434->5432/tcp         Up
scrapeagent-redis-1       0.0.0.0:6379->6379/tcp         Up
scrapeagent-ollama-1      0.0.0.0:11435->11434/tcp       Up
```

---

## 🔍 **TROUBLESHOOTING**

### **Frontend Not Loading**
- **Check**: `curl http://localhost:8650`
- **Solution**: `docker-compose up -d frontend`
- **Verify**: Navigate to `http://localhost:8650` in browser

### **API Calls Failing**
- **Check**: `curl http://localhost:8601/health`
- **Solution**: `docker-compose up -d swissknife`
- **Verify**: Check API documentation at `http://localhost:8601/docs`

### **Port Conflicts**
If you encounter port conflicts:
1. **Check what's using the port**: `netstat -an | findstr :8650`
2. **Stop conflicting services**: Identify and stop other applications
3. **Restart containers**: `docker-compose down && docker-compose up -d`

---

## ⚠️ **IMPORTANT NOTES**

1. **These ports are PERMANENT** - Do not modify without updating all documentation
2. **All team members MUST use these ports** for consistency
3. **CI/CD pipelines MUST reference these ports** in all configurations
4. **Browser automation tests MUST use port 8650** for frontend testing

---

**Last Updated**: August 6, 2025  
**Version**: 2.2.0  
**Status**: OFFICIAL STANDARD