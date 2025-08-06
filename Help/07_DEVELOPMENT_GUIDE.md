# SwissKnife AI Scraper - Development Guide

## 👨‍💻 **Development Overview**

This guide covers development workflows, code structure, conventions, and best practices for contributing to the SwissKnife AI Scraper project.

---

## 🏗️ **Project Architecture**

### **Code Organization**
```
SwissKnife-AI-Scraper/
├── 📁 api/                     # FastAPI backend
│   ├── routes/                 # API route definitions
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── scraping.py        # Scraping endpoints
│   │   ├── health.py          # Health check endpoints
│   │   └── admin.py           # Admin endpoints
│   └── middleware/            # Custom middleware
├── 📁 core/                   # Core business logic
│   ├── scraper.py             # Main scraper class
│   ├── extraction_engine.py   # Content extraction
│   ├── nlp_processor.py       # NLP processing
│   └── multimodal_processor.py # Multimodal handling
├── 📁 services/               # External service integrations
│   ├── crawl4ai_client.py     # Crawl4AI integration
│   ├── jina_ai_client.py      # Jina AI integration
│   ├── llm_manager.py         # LLM management
│   └── performance_optimizer.py # Performance optimization
├── 📁 features/               # Feature implementations
│   ├── conversation_manager.py # Multi-step conversations
│   ├── proxy_manager.py       # Proxy management
│   └── batch_processor.py     # Batch processing
├── 📁 frontend/               # React frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   ├── store/             # Redux store
│   │   └── types/             # TypeScript types
│   └── public/                # Static assets
├── 📁 config/                 # Configuration files
├── 📁 utils/                  # Utility functions
├── 📁 tests/                  # Test files
└── 📁 Help/                   # Documentation
```

### **Design Patterns**

#### **Backend Patterns**
- **Dependency Injection**: FastAPI's dependency system for service management
- **Repository Pattern**: Data access abstraction
- **Factory Pattern**: Service instantiation and configuration
- **Observer Pattern**: Event-driven processing
- **Strategy Pattern**: Multiple extraction strategies

#### **Frontend Patterns**
- **Component Composition**: Reusable React components
- **Container/Presenter**: Separation of logic and presentation
- **Redux Pattern**: Centralized state management
- **Hook Pattern**: Custom React hooks for shared logic
- **Higher-Order Components**: Cross-cutting concerns

---

## 🔧 **Development Environment**

### **Backend Development Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Start development services
docker-compose up -d postgres redis crawl4ai ollama

# Run backend in development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8601
```

### **Frontend Development Setup**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Or with yarn
yarn install
yarn start
```

### **Development Tools**

#### **Backend Tools**
- **IDE**: VS Code, PyCharm, or similar
- **Linting**: flake8, black, isort
- **Type Checking**: mypy
- **Testing**: pytest, pytest-asyncio
- **Debugging**: pdb, VS Code debugger
- **API Testing**: Postman, Insomnia, or curl

#### **Frontend Tools**
- **IDE**: VS Code, WebStorm, or similar
- **Linting**: ESLint, Prettier
- **Type Checking**: TypeScript compiler
- **Testing**: Jest, React Testing Library
- **Debugging**: Browser DevTools, React DevTools
- **State Management**: Redux DevTools

---

## 📝 **Coding Standards**

### **Python Code Style**

#### **Formatting**
```python
# Use Black formatter with line length 88
# Example: properly formatted Python code

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

class ScrapeRequest(BaseModel):
    """Request model for scraping operations."""
    
    url: str = Field(..., description="Target URL to scrape")
    query: Optional[str] = Field(None, description="Natural language query")
    options: Dict[str, Any] = Field(default_factory=dict)

async def scrape_url(
    request: ScrapeRequest,
    scraper: SwissKnifeScraper = Depends(get_scraper)
) -> Dict[str, Any]:
    """
    Scrape URL with given parameters.
    
    Args:
        request: Scraping request parameters
        scraper: Injected scraper instance
        
    Returns:
        Scraping results dictionary
        
    Raises:
        HTTPException: If scraping fails
    """
    try:
        result = await scraper.scrape(
            url=request.url,
            query=request.query,
            options=request.options
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### **Naming Conventions**
```python
# Classes: PascalCase
class SwissKnifeScraper:
    pass

# Functions and variables: snake_case
def extract_content(html_content: str) -> str:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_CONCURRENT_REQUESTS = 10
DEFAULT_TIMEOUT = 30

# Private methods: leading underscore
def _internal_method(self) -> None:
    pass
```

### **TypeScript Code Style**

#### **Formatting**
```typescript
// Use Prettier with 2-space indentation
// Example: properly formatted TypeScript code

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

class APIClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = 'http://localhost:8601') {
    this.baseUrl = baseUrl
  }

  async scrapeUrl(request: ScrapeRequest): Promise<ScrapeResponse> {
    const response = await fetch(`${this.baseUrl}/scrape`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }
}
```

#### **Naming Conventions**
```typescript
// Interfaces: PascalCase with 'I' prefix (optional)
interface User {
  id: string
  email: string
}

// Types: PascalCase
type AuthState = 'authenticated' | 'unauthenticated' | 'loading'

// Functions and variables: camelCase
const getUserData = async (userId: string): Promise<User> => {
  // implementation
}

// Constants: UPPER_SNAKE_CASE
const API_BASE_URL = 'http://localhost:8601'
const MAX_RETRY_ATTEMPTS = 3

// React components: PascalCase
const UserProfile: React.FC<UserProfileProps> = ({ user }) => {
  return <div>{user.email}</div>
}
```

---

## 🧪 **Testing Guidelines**

### **Backend Testing**

#### **Test Structure**
```python
# tests/test_scraper.py
import pytest
from unittest.mock import AsyncMock, patch
from core.scraper import SwissKnifeScraper

class TestSwissKnifeScraper:
    """Test suite for SwissKnifeScraper class."""
    
    @pytest.fixture
    async def scraper(self):
        """Create scraper instance for testing."""
        scraper = SwissKnifeScraper()
        await scraper.initialize()
        yield scraper
        await scraper.cleanup()
    
    @pytest.mark.asyncio
    async def test_basic_scraping(self, scraper):
        """Test basic URL scraping functionality."""
        # Arrange
        url = "https://example.com"
        expected_content = {"title": "Example", "text": "Sample content"}
        
        # Mock external dependencies
        with patch.object(scraper.crawl4ai_client, 'crawl') as mock_crawl:
            mock_crawl.return_value = expected_content
            
            # Act
            result = await scraper.scrape(url)
            
            # Assert
            assert result["success"] is True
            assert "data" in result
            mock_crawl.assert_called_once_with(url, {})
    
    @pytest.mark.asyncio
    async def test_natural_language_scraping(self, scraper):
        """Test natural language query processing."""
        # Test implementation
        pass
    
    @pytest.mark.asyncio
    async def test_error_handling(self, scraper):
        """Test error handling in scraping operations."""
        # Test implementation
        pass
```

#### **Test Categories**
```python
# Unit tests: Test individual functions/methods
@pytest.mark.unit
async def test_extract_text():
    pass

# Integration tests: Test component interactions
@pytest.mark.integration
async def test_scraper_with_crawl4ai():
    pass

# End-to-end tests: Test complete workflows
@pytest.mark.e2e
async def test_complete_scraping_workflow():
    pass
```

### **Frontend Testing**

#### **Component Testing**
```typescript
// src/components/__tests__/LoginForm.test.tsx
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { store } from '../../store'
import LoginForm from '../LoginForm'

describe('LoginForm', () => {
  const renderWithProvider = (component: React.ReactElement) => {
    return render(
      <Provider store={store}>
        {component}
      </Provider>
    )
  }

  test('renders login form correctly', () => {
    renderWithProvider(<LoginForm />)
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  test('handles form submission', async () => {
    const mockLogin = jest.fn()
    renderWithProvider(<LoginForm onLogin={mockLogin} />)
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' }
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' }
    })
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
    })
  })
})
```

#### **API Service Testing**
```typescript
// src/services/__tests__/apiClient.test.ts
import { APIClient } from '../apiClient'

describe('APIClient', () => {
  let apiClient: APIClient
  
  beforeEach(() => {
    apiClient = new APIClient('http://localhost:8601')
  })

  test('scrapeUrl makes correct API call', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true, data: {} })
    })
    global.fetch = mockFetch

    const request = {
      url: 'https://example.com',
      query: 'Extract all text'
    }

    await apiClient.scrapeUrl(request)

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8601/scrape',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        }),
        body: JSON.stringify(request)
      })
    )
  })
})
```

---

## 🔄 **Development Workflow**

### **Git Workflow**

#### **Branch Strategy**
```bash
# Main branches
main          # Production-ready code
develop       # Integration branch for features

# Feature branches
feature/auth-system
feature/nlp-processing
feature/multimodal-support

# Hotfix branches
hotfix/security-patch
hotfix/critical-bug-fix

# Release branches
release/v2.2.0
release/v2.3.0
```

#### **Commit Conventions**
```bash
# Commit message format
<type>(<scope>): <description>

# Types
feat:     # New feature
fix:      # Bug fix
docs:     # Documentation changes
style:    # Code style changes (formatting, etc.)
refactor: # Code refactoring
test:     # Adding or updating tests
chore:    # Maintenance tasks

# Examples
feat(auth): add JWT token refresh functionality
fix(scraper): resolve memory leak in batch processing
docs(api): update endpoint documentation
test(frontend): add authentication flow tests
```

### **Development Process**

#### **Feature Development**
```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Develop feature with tests
# - Write failing tests first (TDD)
# - Implement feature
# - Ensure all tests pass
# - Update documentation

# 3. Code review process
git push origin feature/new-feature
# Create pull request
# Address review feedback

# 4. Merge to develop
git checkout develop
git merge feature/new-feature
git push origin develop

# 5. Deploy to staging for testing
# 6. Merge to main for production
```

#### **Code Review Checklist**
- [ ] **Functionality**: Does the code work as expected?
- [ ] **Tests**: Are there adequate tests with good coverage?
- [ ] **Documentation**: Is the code well-documented?
- [ ] **Performance**: Are there any performance concerns?
- [ ] **Security**: Are there any security vulnerabilities?
- [ ] **Style**: Does the code follow project conventions?
- [ ] **Dependencies**: Are new dependencies necessary and secure?

---

## 🚀 **Deployment Process**

### **Development Deployment**
```bash
# Deploy to development environment
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
docker-compose exec swissknife alembic upgrade head

# Verify deployment
curl http://localhost:8601/health
```

### **Staging Deployment**
```bash
# Deploy to staging environment
docker-compose -f docker-compose.staging.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Performance testing
# Load testing with appropriate tools
```

### **Production Deployment**
```bash
# Deploy to production environment
docker-compose -f docker-compose.prod.yml up -d

# Health checks
curl https://api.yourdomain.com/health

# Monitor logs and metrics
docker-compose logs -f swissknife
```

---

## 🔍 **Debugging Guidelines**

### **Backend Debugging**

#### **Logging Configuration**
```python
# utils/logger.py
import logging
import structlog

def setup_logger(name: str, level: str = "INFO") -> structlog.BoundLogger:
    """Configure structured logging."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper())
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger(name)

# Usage in code
logger = setup_logger(__name__)

async def scrape_url(url: str):
    logger.info("Starting scrape operation", url=url)
    try:
        result = await perform_scrape(url)
        logger.info("Scrape completed successfully", 
                   url=url, 
                   items_found=len(result))
        return result
    except Exception as e:
        logger.error("Scrape operation failed", 
                    url=url, 
                    error=str(e), 
                    exc_info=True)
        raise
```

#### **Debug Configuration**
```python
# For development debugging
if settings.DEBUG:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("Waiting for debugger attach...")
    debugpy.wait_for_client()
```

### **Frontend Debugging**

#### **Redux DevTools**
```typescript
// store/index.ts
import { configureStore } from '@reduxjs/toolkit'
import { authSlice } from './slices/authSlice'

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    // other reducers
  },
  devTools: process.env.NODE_ENV !== 'production',
})
```

#### **Error Boundaries**
```typescript
// components/ErrorBoundary.tsx
import React from 'react'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    // Send to error reporting service
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong.</h2>
          <details>
            {this.state.error?.message}
          </details>
        </div>
      )
    }

    return this.props.children
  }
}
```

---

## 📊 **Performance Optimization**

### **Backend Performance**

#### **Async/Await Best Practices**
```python
# Good: Concurrent execution
async def process_multiple_urls(urls: List[str]) -> List[Dict]:
    tasks = [scrape_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

# Good: Database connection pooling
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

#### **Caching Strategies**
```python
# Redis caching decorator
from functools import wraps
import json

def cache_result(ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(result, default=str)
            )
            return result
        return wrapper
    return decorator

@cache_result(ttl=1800)
async def expensive_operation(param: str) -> Dict:
    # Expensive computation
    pass
```

### **Frontend Performance**

#### **Code Splitting**
```typescript
// Lazy loading components
import { lazy, Suspense } from 'react'

const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ProjectsPage = lazy(() => import('./pages/ProjectsPage'))

function App() {
  return (
    <Router>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
        </Routes>
      </Suspense>
    </Router>
  )
}
```

#### **Memoization**
```typescript
// React.memo for component memoization
const ExpensiveComponent = React.memo(({ data, onUpdate }) => {
  return (
    <div>
      {/* Expensive rendering logic */}
    </div>
  )
})

// useMemo for expensive calculations
const ProcessedData = ({ rawData }) => {
  const processedData = useMemo(() => {
    return rawData.map(item => ({
      ...item,
      processed: expensiveProcessing(item)
    }))
  }, [rawData])

  return <div>{/* Render processed data */}</div>
}
```

---

## 📚 **Documentation Standards**

### **Code Documentation**
```python
# Python docstring format (Google style)
def extract_content(html: str, selector: str = None) -> Dict[str, Any]:
    """
    Extract content from HTML using CSS selectors.
    
    Args:
        html: Raw HTML content to process
        selector: Optional CSS selector for targeted extraction
        
    Returns:
        Dictionary containing extracted content with metadata
        
    Raises:
        ValueError: If HTML is empty or invalid
        ExtractionError: If extraction fails
        
    Example:
        >>> html = "<div class='content'>Hello World</div>"
        >>> result = extract_content(html, ".content")
        >>> print(result['text'])
        'Hello World'
    """
    if not html.strip():
        raise ValueError("HTML content cannot be empty")
    
    # Implementation
    pass
```

```typescript
// TypeScript JSDoc format
/**
 * Scrape URL with natural language query
 * 
 * @param url - Target URL to scrape
 * @param query - Natural language query describing what to extract
 * @param options - Additional scraping options
 * @returns Promise resolving to scraping results
 * 
 * @example
 * ```typescript
 * const result = await scrapeUrl(
 *   'https://example.com',
 *   'Extract all product prices'
 * )
 * console.log(result.data.products)
 * ```
 */
async function scrapeUrl(
  url: string,
  query: string,
  options: ScrapeOptions = {}
): Promise<ScrapeResponse> {
  // Implementation
}
```

### **API Documentation**
```python
# FastAPI automatic documentation
@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(
    request: ScrapeRequest,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """
    Scrape URL with intelligent content extraction.
    
    This endpoint provides adaptive content extraction using multiple strategies:
    - Basic HTML parsing for simple content
    - Natural language processing for complex queries
    - Multimodal processing for rich content
    
    **Example Request:**
    ```json
    {
        "url": "https://example.com",
        "query": "Extract all product information",
        "options": {
            "format": "json",
            "include_metadata": true
        }
    }
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "data": {
            "products": [...],
            "metadata": {...}
        },
        "execution_time": 2.5
    }
    ```
    """
    # Implementation
```

---

## 🎯 **Best Practices Summary**

### **Code Quality**
1. **Write tests first** (Test-Driven Development)
2. **Keep functions small** and focused on single responsibility
3. **Use type hints** in Python and TypeScript
4. **Handle errors gracefully** with proper exception handling
5. **Document public APIs** thoroughly
6. **Follow SOLID principles** for maintainable code

### **Performance**
1. **Use async/await** for I/O operations
2. **Implement caching** for expensive operations
3. **Optimize database queries** with proper indexing
4. **Use connection pooling** for external services
5. **Monitor performance metrics** continuously

### **Security**
1. **Validate all inputs** at API boundaries
2. **Use parameterized queries** to prevent SQL injection
3. **Implement proper authentication** and authorization
4. **Keep dependencies updated** and scan for vulnerabilities
5. **Log security events** for monitoring

### **Maintainability**
1. **Keep code DRY** (Don't Repeat Yourself)
2. **Use meaningful names** for variables and functions
3. **Refactor regularly** to improve code quality
4. **Maintain comprehensive documentation**
5. **Use version control effectively** with meaningful commits

---

**This development guide ensures consistent, high-quality code across the SwissKnife AI Scraper project. Follow these guidelines to contribute effectively and maintain the project's standards.**

---

**Last Updated**: August 6, 2025  
**Version**: 2.2.0