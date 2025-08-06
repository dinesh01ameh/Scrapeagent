# SwissKnife AI Scraper - Project Index

## 📚 **Master Index of All Components**

This document provides a comprehensive index of all modules, classes, functions, APIs, and components in the SwissKnife AI Scraper project for easy navigation and reference.

---

## 🏗️ **Project Structure Index**

### **Root Directory**
```
SwissKnife-AI-Scraper/
├── 📄 main.py                     # Application entry point
├── 📄 requirements.txt            # Python dependencies
├── 📄 docker-compose.yml          # Docker services configuration
├── 📄 Dockerfile                  # Backend container definition
├── 📄 .env.example               # Environment variables template
├── 📄 .gitignore                 # Git ignore rules
├── 📄 README.md                  # Project overview
└── 📄 LICENSE                    # Project license
```

---

## 🔧 **Backend Components Index**

### **API Routes (`api/routes/`)**

#### **Authentication Routes (`api/routes/auth.py`)**
| Endpoint | Method | Function | Description |
|----------|--------|----------|-------------|
| `/auth/login` | POST | `login()` | User authentication |
| `/auth/register` | POST | `register()` | User registration |
| `/auth/validate` | POST | `validate_token()` | Token validation |
| `/auth/refresh` | POST | `refresh_token()` | Token refresh |
| `/auth/me` | GET | `get_current_user()` | Get user info |
| `/auth/forgot-password` | POST | `forgot_password()` | Password reset request |
| `/auth/reset-password` | POST | `reset_password()` | Password reset |

**Key Classes:**
- `LoginRequest` - Login request model
- `RegisterRequest` - Registration request model
- `TokenResponse` - Authentication response model
- `ValidationRequest` - Token validation model
- `PasswordResetRequest` - Password reset model

**Key Functions:**
- `verify_password()` - Password verification
- `get_password_hash()` - Password hashing
- `create_access_token()` - JWT token creation
- `verify_token()` - JWT token verification

#### **Scraping Routes (`api/routes/scraping.py`)**
| Endpoint | Method | Function | Description |
|----------|--------|----------|-------------|
| `/scrape` | POST | `scrape_url()` | Basic URL scraping |
| `/natural-language-scrape` | POST | `natural_language_scrape()` | NL query scraping |
| `/multimodal-scrape` | POST | `multimodal_scrape()` | Multi-format extraction |
| `/resolve-ambiguity` | POST | `resolve_ambiguous_query()` | Query clarification |
| `/batch-scrape` | POST | `batch_scrape()` | Batch processing |
| `/batch-scrape/{id}/status` | GET | `get_job_status()` | Batch job status |
| `/conversation/start` | POST | `start_multi_step_conversation()` | Start conversation |
| `/conversation/continue` | POST | `continue_multi_step_conversation()` | Continue conversation |
| `/conversation/{id}/summary` | GET | `get_conversation_summary()` | Conversation summary |

**Key Classes:**
- `ScrapeRequest` - Basic scrape request
- `NaturalLanguageScrapeRequest` - NL scrape request
- `MultiModalScrapeRequest` - Multimodal request
- `AmbiguityResolutionRequest` - Ambiguity resolution
- `ScrapeResponse` - Scraping response model

#### **Health Routes (`api/routes/health.py`)**
| Endpoint | Method | Function | Description |
|----------|--------|----------|-------------|
| `/health` | GET | `health_check()` | Basic health status |
| `/health/detailed` | GET | `detailed_health_check()` | Comprehensive health |
| `/status` | GET | `get_system_status()` | System metrics |

#### **Admin Routes (`api/routes/admin.py`)**
| Endpoint | Method | Function | Description |
|----------|--------|----------|-------------|
| `/admin/stats` | GET | `get_system_stats()` | System statistics |
| `/admin/users` | GET | `list_users()` | User management |
| `/admin/cleanup` | POST | `cleanup_old_sessions()` | System cleanup |

### **Core Modules (`core/`)**

#### **Main Scraper (`core/scraper.py`)**
**SwissKnifeScraper Class:**
- `__init__()` - Initialize scraper instance
- `initialize()` - Async initialization of services
- `scrape()` - Main scraping method with intelligent routing
- `natural_language_scrape()` - NLP-powered content extraction
- `multimodal_scrape()` - Multi-format content processing
- `resolve_ambiguous_query()` - Query clarification system
- `get_status()` - System health and performance metrics
- `cleanup()` - Resource cleanup and session management
- `__aenter__()` / `__aexit__()` - Async context manager

**Key Properties:**
- `crawl4ai_client` - Crawl4AI service integration
- `jina_ai_client` - Jina AI service integration
- `llm_manager` - Local LLM management
- `extraction_engine` - Content extraction engine
- `nlp_processor` - Natural language processing
- `multimodal_processor` - Multimodal content handler
- `performance_optimizer` - Performance optimization
- `proxy_manager` - Proxy rotation management

#### **Extraction Engine (`core/extraction_engine.py`)**
**ExtractionEngine Class:**
- `extract_structured_data()` - Schema-based extraction
- `extract_text_content()` - Clean text extraction
- `extract_metadata()` - Page metadata extraction
- `extract_links()` - Link extraction with filtering
- `extract_images()` - Image extraction and processing
- `extract_tables()` - Table data extraction
- `extract_forms()` - Form structure extraction

#### **NLP Processor (`core/nlp_processor.py`)**
**NLPProcessor Class:**
- `analyze_query()` - Query intent analysis
- `extract_entities()` - Named entity recognition
- `resolve_ambiguity()` - Ambiguity resolution
- `generate_extraction_schema()` - Schema from natural language
- `classify_intent()` - Intent classification
- `assess_complexity()` - Query complexity assessment

#### **Multimodal Processor (`core/multimodal_processor.py`)**
**MultiModalProcessor Class:**
- `process_text()` - Text processing and analysis
- `process_images()` - Image analysis and OCR
- `process_documents()` - Document parsing
- `process_audio()` - Audio content processing
- `process_video()` - Video content analysis
- `combine_modalities()` - Multi-modal result integration

### **Service Integrations (`services/`)**

#### **Crawl4AI Client (`services/crawl4ai_client.py`)**
**Crawl4AIClient Class:**
- `crawl()` - Basic crawling with Playwright
- `extract_structured()` - Structured data extraction
- `batch_crawl()` - Batch processing
- `get_status()` - Service health check
- `configure_session()` - Session configuration
- `handle_javascript()` - JavaScript rendering

#### **Jina AI Client (`services/jina_ai_client.py`)**
**JinaAIClient Class:**
- `read_url()` - Jina Reader API integration
- `search_content()` - Jina Search API integration
- `process_multimodal()` - Multi-modal processing
- `enhance_extraction()` - AI-enhanced extraction
- `summarize_content()` - Content summarization

#### **LLM Manager (`services/llm_manager.py`)**
**LLMManager Class:**
- `process_query()` - Query processing with LLM
- `generate_schema()` - Schema generation
- `summarize_content()` - Content summarization
- `resolve_ambiguity()` - Ambiguity resolution
- `classify_intent()` - Intent classification
- `extract_entities()` - Entity extraction

#### **Performance Optimizer (`services/performance_optimizer.py`)**
**PerformanceOptimizer Class:**
- `cache_result()` - Result caching
- `get_cached_result()` - Cache retrieval
- `optimize_batch()` - Batch optimization
- `monitor_performance()` - Performance monitoring
- `manage_resources()` - Resource management

### **Feature Modules (`features/`)**

#### **Conversation Manager (`features/conversation_manager.py`)**
**ConversationManager Class:**
- `start_conversation()` - Start new conversation
- `continue_conversation()` - Continue conversation
- `get_conversation_summary()` - Get summary
- `predict_next_intent()` - Intent prediction
- `manage_context()` - Context management

#### **Proxy Manager (`features/proxy_manager.py`)**
**ProxyManager Class:**
- `get_proxy()` - Get suitable proxy
- `rotate_proxy()` - Rotate proxy for session
- `check_proxy_health()` - Proxy health check
- `manage_proxy_pool()` - Pool management
- `configure_proxy()` - Proxy configuration

#### **Batch Processor (`features/batch_processor.py`)**
**BatchProcessor Class:**
- `submit_batch()` - Submit batch job
- `get_batch_status()` - Check batch status
- `process_batch_results()` - Process results
- `cancel_batch()` - Cancel batch job
- `optimize_batch_size()` - Batch size optimization

### **Configuration (`config/`)**

#### **Settings (`config/settings.py`)**
**Settings Class:**
- `API_V1_STR` - API version prefix
- `SECRET_KEY` - JWT secret key
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection string
- `CRAWL4AI_BASE_URL` - Crawl4AI service URL
- `JINA_AI_API_KEY` - Jina AI API key
- `OLLAMA_BASE_URL` - Ollama service URL

#### **Database (`config/database.py`)**
- `engine` - SQLAlchemy async engine
- `AsyncSessionLocal` - Session factory
- `get_db()` - Database session dependency

### **Utilities (`utils/`)**

#### **Logger (`utils/logger.py`)**
- `setup_logger()` - Configure structured logging
- `get_logger()` - Get logger instance

#### **Validators (`utils/validators.py`)**
- `validate_url()` - URL format validation
- `validate_email()` - Email format validation
- `validate_password()` - Password strength validation

#### **Helpers (`utils/helpers.py`)**
- `generate_session_id()` - Generate unique session ID
- `format_response()` - Format API response
- `hash_url()` - Generate URL hash
- `sanitize_input()` - Input sanitization

---

## 🎨 **Frontend Components Index**

### **Main Application (`frontend/src/`)**

#### **App Component (`frontend/src/App.tsx`)**
- Main application component with routing
- Theme provider setup
- Global error boundary
- Authentication context provider

#### **Entry Point (`frontend/src/index.tsx`)**
- React application bootstrap
- Redux store provider
- Service worker registration

### **Pages (`frontend/src/pages/`)**

#### **Authentication Pages (`frontend/src/pages/auth/`)**
**LoginPage (`LoginPage.tsx`):**
- User login interface
- Form validation
- Error handling
- Redirect logic

**RegisterPage (`RegisterPage.tsx`):**
- User registration interface
- Multi-step form
- Terms acceptance
- Email validation

#### **Dashboard (`frontend/src/pages/dashboard/`)**
**DashboardPage (`DashboardPage.tsx`):**
- Main dashboard interface
- Statistics cards
- Recent activity
- Quick actions
- System status

#### **Projects (`frontend/src/pages/projects/`)**
**ProjectsPage (`ProjectsPage.tsx`):**
- Project management interface
- Project creation
- Project listing
- Project details

#### **Jobs (`frontend/src/pages/jobs/`)**
**JobsPage (`JobsPage.tsx`):**
- Job management interface
- Job creation
- Job monitoring
- Job results

#### **Content (`frontend/src/pages/content/`)**
**ContentPage (`ContentPage.tsx`):**
- Content management interface
- Content viewing
- Export functionality
- Search and filtering

#### **Settings (`frontend/src/pages/settings/`)**
**SettingsPage (`SettingsPage.tsx`):**
- User settings
- System configuration
- API key management
- Preferences

### **Components (`frontend/src/components/`)**

#### **Layout Components (`frontend/src/components/layout/`)**
**Header (`Header.tsx`):**
- Navigation header
- User menu
- Search functionality
- Notifications

**Sidebar (`Sidebar.tsx`):**
- Navigation sidebar
- Menu items
- Collapsible design
- Active state management

**Layout (`Layout.tsx`):**
- Main layout wrapper
- Header and sidebar integration
- Content area
- Responsive design

#### **Authentication Components (`frontend/src/components/auth/`)**
**ProtectedRoute (`ProtectedRoute.tsx`):**
- Route protection
- Authentication checking
- Redirect logic
- Loading states

### **Services (`frontend/src/services/`)**

#### **API Client (`frontend/src/services/apiClient.ts`)**
**APIClient Class:**
- `login()` - User authentication
- `register()` - User registration
- `scrapeUrl()` - URL scraping
- `naturalLanguageScrape()` - NL scraping
- `multimodalScrape()` - Multimodal scraping
- `getJobs()` - Job management
- `getProjects()` - Project management

#### **Authentication Service (`frontend/src/services/authService.ts`)**
- `login()` - Login functionality
- `register()` - Registration functionality
- `logout()` - Logout functionality
- `getToken()` - Token management
- `isAuthenticated()` - Authentication status

#### **Dashboard Service (`frontend/src/services/dashboardService.ts`)**
- `getDashboardData()` - Dashboard statistics
- `getRecentActivity()` - Recent activity
- `getSystemStatus()` - System health

### **State Management (`frontend/src/store/`)**

#### **Store (`frontend/src/store/index.ts`)**
- Redux store configuration
- Middleware setup
- DevTools integration

#### **Auth Slice (`frontend/src/store/slices/authSlice.ts`)**
**State:**
- `user` - Current user data
- `token` - JWT token
- `isAuthenticated` - Authentication status
- `loading` - Loading state
- `error` - Error messages

**Actions:**
- `login` - Login action
- `logout` - Logout action
- `setUser` - Set user data
- `setError` - Set error message
- `clearError` - Clear error

#### **Projects Slice (`frontend/src/store/slices/projectsSlice.ts`)**
**State:**
- `projects` - Project list
- `currentProject` - Selected project
- `loading` - Loading state
- `error` - Error messages

#### **Jobs Slice (`frontend/src/store/slices/jobsSlice.ts`)**
**State:**
- `jobs` - Job list
- `currentJob` - Selected job
- `loading` - Loading state
- `error` - Error messages

### **Types (`frontend/src/types/`)**

#### **Type Definitions (`frontend/src/types/index.ts`)**
```typescript
// User types
interface User {
  id: string
  email: string
  full_name: string
  username?: string
}

// Authentication types
interface LoginCredentials {
  email: string
  password: string
}

interface RegisterData {
  email: string
  password: string
  full_name: string
  username?: string
}

// Scraping types
interface ScrapeRequest {
  url: string
  query?: string
  options?: Record<string, any>
}

interface ScrapeResponse {
  success: boolean
  data?: any
  error?: string
  executionTime?: number
}

// Project types
interface Project {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

// Job types
interface Job {
  id: string
  project_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
}
```

---

## 🗄️ **Database Schema Index**

### **Tables**

#### **Users Table**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Projects Table**
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Scraping Jobs Table**
```sql
CREATE TABLE scraping_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(2048) NOT NULL,
    query TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Scraped Content Table**
```sql
CREATE TABLE scraped_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    url VARCHAR(2048) NOT NULL,
    url_hash VARCHAR(64) NOT NULL,
    title VARCHAR(500),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    content_type VARCHAR(100),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Indexes**
```sql
-- Performance indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_jobs_project_id ON scraping_jobs(project_id);
CREATE INDEX idx_jobs_status ON scraping_jobs(status);
CREATE INDEX idx_jobs_created_at ON scraping_jobs(created_at);
CREATE INDEX idx_content_url_hash ON scraped_content(url_hash);
CREATE INDEX idx_content_job_id ON scraped_content(job_id);
```

---

## 🐳 **Docker Configuration Index**

### **Services**
| Service | Container | Port | Image | Purpose |
|---------|-----------|------|-------|---------|
| frontend | scrapeagent-frontend-1 | 8650:80 | Custom React | User interface |
| swissknife | scrapeagent-swissknife-1 | 8601:8601 | Custom FastAPI | Backend API |
| crawl4ai | swissknife-crawl4ai | 11235:11235 | unclecode/crawl4ai | Scraping engine |
| postgres | scrapeagent-postgres-1 | 5434:5432 | postgres:15-alpine | Database |
| redis | scrapeagent-redis-1 | 6379:6379 | redis:7-alpine | Cache & sessions |
| ollama | scrapeagent-ollama-1 | 11435:11434 | ollama/ollama | Local LLM |

### **Volumes**
- `postgres_data` - Database persistence
- `redis_data` - Redis persistence
- `crawl4ai_data` - Crawl4AI data
- `swissknife_data` - Application data
- `swissknife_logs` - Application logs

### **Networks**
- `swissknife-network` - Internal service communication

---

## 📊 **API Endpoints Summary**

### **Authentication Endpoints**
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/validate` - Token validation
- `POST /auth/refresh` - Token refresh
- `GET /auth/me` - Current user info

### **Scraping Endpoints**
- `POST /scrape` - Basic scraping
- `POST /natural-language-scrape` - NL scraping
- `POST /multimodal-scrape` - Multimodal scraping
- `POST /resolve-ambiguity` - Query resolution
- `POST /batch-scrape` - Batch processing
- `GET /batch-scrape/{id}/status` - Batch status

### **System Endpoints**
- `GET /health` - Health check
- `GET /health/detailed` - Detailed health
- `GET /status` - System status
- `GET /metrics` - Performance metrics

### **Admin Endpoints**
- `GET /admin/stats` - System statistics
- `GET /admin/users` - User management
- `POST /admin/cleanup` - System cleanup

---

## 🔗 **Cross-Reference Index**

### **Authentication Flow**
1. **Frontend**: `LoginPage.tsx` → `authService.login()`
2. **API**: `POST /auth/login` → `auth.py:login()`
3. **Backend**: JWT token generation → Redis session storage
4. **Frontend**: Token storage → `authSlice` state update
5. **Protection**: `ProtectedRoute.tsx` → Token validation

### **Scraping Flow**
1. **Frontend**: User input → `ScrapeForm` component
2. **API**: `POST /scrape` → `scraping.py:scrape_url()`
3. **Core**: `SwissKnifeScraper.scrape()` → Service orchestration
4. **Services**: Crawl4AI → Jina AI → LLM processing
5. **Storage**: Results → PostgreSQL → Frontend display

### **Data Flow**
1. **Input**: User request → Frontend validation
2. **API**: Request → Backend processing
3. **Processing**: Core services → External APIs
4. **Storage**: Results → Database/Cache
5. **Output**: Response → Frontend display

---

## 📚 **Documentation Cross-Reference**

### **Related Documentation**
- **[Project Overview](./01_PROJECT_OVERVIEW.md)** - System architecture
- **[Module Documentation](./02_MODULE_DOCUMENTATION.md)** - Detailed modules
- **[API Reference](./03_API_REFERENCE.md)** - Complete API docs
- **[Port Configuration](./04_PORT_CONFIGURATION.md)** - Service ports
- **[Feature Documentation](./05_FEATURE_DOCUMENTATION.md)** - Feature guides
- **[Setup Guide](./06_SETUP_INSTALLATION.md)** - Installation steps
- **[Development Guide](./07_DEVELOPMENT_GUIDE.md)** - Development workflow
- **[Deployment Guide](./08_DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Troubleshooting](./09_TROUBLESHOOTING.md)** - Common issues

### **Quick Navigation**
- **Authentication**: See sections in modules 2, 3, 5, 9
- **Scraping**: See sections in modules 1, 2, 3, 5
- **Frontend**: See sections in modules 2, 5, 7
- **Backend**: See sections in modules 1, 2, 3, 7
- **Deployment**: See modules 6, 8
- **Troubleshooting**: See module 9

---

## 🎯 **Quick Reference**

### **Key URLs**
- **Frontend**: http://localhost:8650
- **Backend API**: http://localhost:8601
- **API Docs**: http://localhost:8601/docs
- **Health Check**: http://localhost:8601/health

### **Key Commands**
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f service-name

# Health check
curl http://localhost:8601/health

# Run tests
pytest tests/ -v

# Build frontend
cd frontend && npm run build
```

### **Key Files**
- **Main entry**: `main.py`
- **Core scraper**: `core/scraper.py`
- **API routes**: `api/routes/`
- **Frontend app**: `frontend/src/App.tsx`
- **Configuration**: `config/settings.py`
- **Docker setup**: `docker-compose.yml`

---

**This comprehensive index provides complete navigation and reference for all components in the SwissKnife AI Scraper project. Use this as your primary reference for understanding the project structure and finding specific components.**

---

**Last Updated**: August 6, 2025  
**Version**: 2.2.0  
**Total Components Indexed**: 200+