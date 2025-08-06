# SwissKnife AI Scraper - Module Documentation

## 📚 **Module Overview**

This document provides comprehensive documentation for all modules in the SwissKnife AI Scraper project, including their purpose, key classes, methods, and usage examples.

---

## 🔧 **Core Modules**

### **1. core/scraper.py - Main Scraper Engine**

#### **SwissKnifeScraper Class**
The central orchestrator for all scraping operations, integrating multiple AI services and processing engines.

**Key Methods:**
- `__init__(self)` - Initialize scraper with all required services
- `initialize(self)` - Async initialization of all components
- `scrape(self, url, options)` - Main scraping method with intelligent routing
- `natural_language_scrape(self, query, url)` - NLP-powered content extraction
- `multimodal_scrape(self, url, modalities)` - Multi-format content processing
- `resolve_ambiguous_query(self, query, context)` - Query clarification
- `get_status(self)` - System health and performance metrics
- `cleanup(self)` - Resource cleanup and session management

**Key Properties:**
```python
# Core service integrations
self.crawl4ai_client: Crawl4AIClient
self.jina_ai_client: JinaAIClient
self.llm_manager: LLMManager
self.extraction_engine: ExtractionEngine
self.nlp_processor: NLPProcessor
self.multimodal_processor: MultiModalProcessor
self.performance_optimizer: PerformanceOptimizer
self.proxy_manager: ProxyManager

# State management
self.is_initialized: bool
self.initialization_time: Optional[datetime]
self.active_sessions: Dict[str, Any]
```

**Usage Example:**
```python
async with SwissKnifeScraper() as scraper:
    await scraper.initialize()
    
    # Basic scraping
    result = await scraper.scrape("https://example.com", {
        "extraction_type": "structured",
        "format": "json"
    })
    
    # Natural language scraping
    nl_result = await scraper.natural_language_scrape(
        "Extract all product prices and descriptions",
        "https://shop.example.com"
    )
```

### **2. core/extraction_engine.py - Content Extraction**

#### **ExtractionEngine Class**
Handles intelligent content extraction with multiple strategies and formats.

**Key Methods:**
- `extract_structured_data(self, html, schema)` - Schema-based extraction
- `extract_text_content(self, html, options)` - Clean text extraction
- `extract_metadata(self, html)` - Page metadata extraction
- `extract_links(self, html, filters)` - Link extraction with filtering
- `extract_images(self, html, options)` - Image extraction and processing

### **3. core/nlp_processor.py - Natural Language Processing**

#### **NLPProcessor Class**
Processes natural language queries and converts them to extraction instructions.

**Key Methods:**
- `analyze_query(self, query)` - Query intent analysis
- `extract_entities(self, text)` - Named entity recognition
- `resolve_ambiguity(self, query, context)` - Ambiguity resolution
- `generate_extraction_schema(self, query)` - Schema generation from NL

### **4. core/multimodal_processor.py - Multimodal Processing**

#### **MultiModalProcessor Class**
Handles processing of multiple content types (text, images, documents).

**Key Methods:**
- `process_text(self, content, options)` - Text processing and analysis
- `process_images(self, images, options)` - Image analysis and OCR
- `process_documents(self, docs, options)` - Document parsing and extraction
- `combine_modalities(self, results)` - Multi-modal result integration

---

## 🌐 **API Modules**

### **1. api/routes/scraping.py - Scraping Endpoints**

#### **Key Endpoints:**

**POST /scrape**
```python
@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest, scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Basic URL scraping with configurable options"""
```

**POST /natural-language-scrape**
```python
@router.post("/natural-language-scrape", response_model=ScrapeResponse)
async def natural_language_scrape(request: NaturalLanguageScrapeRequest, scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Natural language query-based scraping"""
```

**POST /multimodal-scrape**
```python
@router.post("/multimodal-scrape", response_model=ScrapeResponse)
async def multimodal_scrape(request: MultiModalScrapeRequest, scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Multi-format content extraction"""
```

**POST /resolve-ambiguity**
```python
@router.post("/resolve-ambiguity", response_model=ScrapeResponse)
async def resolve_ambiguous_query(request: AmbiguityResolutionRequest, scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Query ambiguity resolution"""
```

#### **Request Models:**
```python
class ScrapeRequest(BaseModel):
    url: str
    extraction_type: str = "basic"
    format: str = "json"
    options: Dict[str, Any] = {}

class NaturalLanguageScrapeRequest(BaseModel):
    query: str
    url: str
    context: Optional[str] = None
    format: str = "json"

class MultiModalScrapeRequest(BaseModel):
    url: str
    modalities: List[str] = ["text", "images"]
    options: Dict[str, Any] = {}
```

### **2. api/routes/auth.py - Authentication Endpoints**

#### **Key Endpoints:**

**POST /auth/login**
```python
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """User authentication with JWT token generation"""
```

**POST /auth/register**
```python
@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """User registration with automatic login"""
```

**POST /auth/validate**
```python
@router.post("/validate", response_model=ValidationResponse)
async def validate_token(request: ValidationRequest):
    """JWT token validation"""
```

#### **Authentication Models:**
```python
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    username: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
```

### **3. api/routes/health.py - Health Check Endpoints**

#### **Key Endpoints:**

**GET /health**
```python
@router.get("/health")
async def health_check():
    """System health status"""
```

**GET /health/detailed**
```python
@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive system status"""
```

---

## 🔌 **Service Modules**

### **1. services/crawl4ai_client.py - Crawl4AI Integration**

#### **Crawl4AIClient Class**
Manages communication with the Crawl4AI Docker service.

**Key Methods:**
- `crawl(self, url, options)` - Basic crawling with Playwright
- `extract_structured(self, url, schema)` - Structured data extraction
- `batch_crawl(self, urls, options)` - Batch processing
- `get_status(self)` - Service health check

**Configuration:**
```python
CRAWL4AI_BASE_URL = "http://localhost:11235"
DEFAULT_OPTIONS = {
    "word_count_threshold": 10,
    "extraction_strategy": "CosineStrategy",
    "chunking_strategy": "RegexChunking"
}
```

### **2. services/jina_ai_client.py - Jina AI Integration**

#### **JinaAIClient Class**
Integrates with Jina AI Reader and Search APIs for enhanced content processing.

**Key Methods:**
- `read_url(self, url, options)` - Jina Reader API integration
- `search_content(self, query, options)` - Jina Search API integration
- `process_multimodal(self, content, modalities)` - Multi-modal processing
- `enhance_extraction(self, content, query)` - AI-enhanced extraction

### **3. services/llm_manager.py - LLM Management**

#### **LLMManager Class**
Manages local and remote LLM interactions for query processing and content analysis.

**Key Methods:**
- `process_query(self, query, context)` - Query processing with LLM
- `generate_schema(self, description)` - Schema generation
- `summarize_content(self, content, options)` - Content summarization
- `resolve_ambiguity(self, query, options)` - Ambiguity resolution

### **4. services/performance_optimizer.py - Performance Optimization**

#### **PerformanceOptimizer Class**
Handles caching, batching, and performance optimization strategies.

**Key Methods:**
- `cache_result(self, key, data, ttl)` - Result caching
- `get_cached_result(self, key)` - Cache retrieval
- `optimize_batch(self, requests)` - Batch optimization
- `monitor_performance(self)` - Performance monitoring

---

## 🎯 **Feature Modules**

### **1. features/conversation_manager.py - Multi-Step Conversations**

#### **ConversationManager Class**
Manages multi-step conversations and context preservation.

**Key Methods:**
- `start_conversation(self, initial_query)` - Start new conversation
- `continue_conversation(self, message, context)` - Continue conversation
- `get_conversation_summary(self, conversation_id)` - Get summary
- `predict_next_intent(self, conversation_id)` - Intent prediction

### **2. features/proxy_manager.py - Proxy Management**

#### **ProxyManager Class**
Handles proxy rotation and management for scraping operations.

**Key Methods:**
- `get_proxy(self, requirements)` - Get suitable proxy
- `rotate_proxy(self, session_id)` - Rotate proxy for session
- `check_proxy_health(self, proxy)` - Proxy health check
- `manage_proxy_pool(self)` - Pool management

### **3. features/batch_processor.py - Batch Processing**

#### **BatchProcessor Class**
Handles batch processing of multiple scraping requests.

**Key Methods:**
- `submit_batch(self, requests)` - Submit batch job
- `get_batch_status(self, batch_id)` - Check batch status
- `process_batch_results(self, batch_id)` - Process results
- `cancel_batch(self, batch_id)` - Cancel batch job

---

## 🎨 **Frontend Modules**

### **1. frontend/src/services/apiClient.ts - API Client**

#### **APIClient Class**
Centralized HTTP client for all API communications.

**Key Methods:**
```typescript
class APIClient {
  // Authentication
  login(credentials: LoginRequest): Promise<TokenResponse>
  register(userData: RegisterRequest): Promise<TokenResponse>
  
  // Scraping
  scrapeUrl(request: ScrapeRequest): Promise<ScrapeResponse>
  naturalLanguageScrape(request: NLScrapeRequest): Promise<ScrapeResponse>
  
  // Job Management
  getJobs(): Promise<Job[]>
  getJobStatus(jobId: string): Promise<JobStatus>
}
```

### **2. frontend/src/services/authService.ts - Authentication Service**

#### **AuthService**
Handles authentication state and token management.

**Key Functions:**
```typescript
// Authentication
export const login = async (credentials: LoginCredentials): Promise<AuthResponse>
export const register = async (userData: RegisterData): Promise<AuthResponse>
export const logout = async (): Promise<void>

// Token Management
export const getToken = (): string | null
export const setToken = (token: string): void
export const isTokenValid = (): boolean
```

### **3. frontend/src/store/slices/ - Redux State Management**

#### **authSlice.ts**
```typescript
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
}

// Actions
export const { login, logout, setUser, setError, clearError } = authSlice.actions
```

#### **projectsSlice.ts**
```typescript
interface ProjectsState {
  projects: Project[]
  currentProject: Project | null
  loading: boolean
  error: string | null
}
```

#### **jobsSlice.ts**
```typescript
interface JobsState {
  jobs: Job[]
  currentJob: Job | null
  loading: boolean
  error: string | null
}
```

---

## 🔧 **Configuration Modules**

### **1. config/settings.py - Application Settings**

#### **Settings Class**
Centralized configuration management using Pydantic.

```python
class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Configuration
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    
    # External Services
    CRAWL4AI_BASE_URL: str = "http://localhost:11235"
    JINA_AI_API_KEY: str
    OLLAMA_BASE_URL: str = "http://localhost:11435"
    
    # Performance Settings
    MAX_CONCURRENT_REQUESTS: int = 10
    CACHE_TTL: int = 3600
    
    class Config:
        env_file = ".env"
```

### **2. config/database.py - Database Configuration**

#### **Database Setup**
SQLAlchemy configuration and session management.

```python
# Database engine
engine = create_async_engine(settings.DATABASE_URL)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Dependency for getting database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

---

## 🧪 **Testing Modules**

### **Test Structure**
```
tests/
├── unit/                   # Unit tests
│   ├── test_scraper.py     # Core scraper tests
│   ├── test_auth.py        # Authentication tests
│   └── test_api.py         # API endpoint tests
├── integration/            # Integration tests
│   ├── test_full_flow.py   # End-to-end tests
│   └── test_services.py    # Service integration tests
└── fixtures/               # Test fixtures and data
    ├── sample_data.json
    └── mock_responses.py
```

### **Key Test Classes**
```python
class TestSwissKnifeScraper:
    """Test core scraper functionality"""
    
class TestAuthenticationAPI:
    """Test authentication endpoints"""
    
class TestScrapingAPI:
    """Test scraping endpoints"""
    
class TestIntegration:
    """Test full system integration"""
```

---

## 📊 **Utility Modules**

### **1. utils/logger.py - Logging Configuration**
```python
def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Configure structured logging"""
```

### **2. utils/validators.py - Input Validation**
```python
def validate_url(url: str) -> bool:
    """Validate URL format"""

def validate_email(email: str) -> bool:
    """Validate email format"""
```

### **3. utils/helpers.py - Helper Functions**
```python
def generate_session_id() -> str:
    """Generate unique session ID"""

def format_response(data: Any, status: str = "success") -> Dict:
    """Format API response"""
```

---

## 🔗 **Module Dependencies**

### **Dependency Graph**
```
main.py
├── api/routes/ (FastAPI endpoints)
│   ├── core/scraper.py (Main scraper)
│   ├── services/ (External integrations)
│   └── features/ (Advanced features)
├── config/settings.py (Configuration)
└── utils/ (Utilities)

frontend/src/
├── components/ (UI components)
├── services/ (API clients)
├── store/ (State management)
└── pages/ (Route components)
```

### **Import Examples**
```python
# Backend imports
from core.scraper import SwissKnifeScraper
from services.crawl4ai_client import Crawl4AIClient
from api.routes.scraping import router as scraping_router
from config.settings import settings

# Frontend imports
import { APIClient } from './services/apiClient'
import { useAuth } from './contexts/AuthContext'
import { store } from './store'
```

---

## 📚 **Usage Examples**

### **Backend Module Usage**
```python
# Initialize and use scraper
async def example_scraping():
    async with SwissKnifeScraper() as scraper:
        await scraper.initialize()
        
        result = await scraper.natural_language_scrape(
            "Find all product prices",
            "https://example-shop.com"
        )
        
        return result
```

### **Frontend Module Usage**
```typescript
// Use API client in component
const MyComponent: React.FC = () => {
  const [data, setData] = useState(null)
  
  useEffect(() => {
    const fetchData = async () => {
      const result = await apiClient.scrapeUrl({
        url: 'https://example.com',
        extraction_type: 'structured'
      })
      setData(result)
    }
    
    fetchData()
  }, [])
  
  return <div>{/* Render data */}</div>
}
```

---

**For detailed API documentation, see [03_API_REFERENCE.md](./03_API_REFERENCE.md)**  
**For setup instructions, see [06_SETUP_INSTALLATION.md](./06_SETUP_INSTALLATION.md)**

---

**Last Updated**: August 6, 2025  
**Version**: 2.2.0