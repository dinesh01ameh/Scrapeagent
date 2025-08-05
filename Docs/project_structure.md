# SwissKnife AI Scraper - Project Structure

## 📁 Directory Structure

```
SwissKnife AI Scraper/
├── 📄 README.md                    # Project documentation
├── 📄 requirements.txt             # Python dependencies
├── 📄 pyproject.toml              # Modern Python project configuration
├── 📄 .env.example                # Environment variables template
├── 📄 .gitignore                  # Git ignore rules
├── 📄 Dockerfile                  # Docker container configuration
├── 📄 docker-compose.yml          # Multi-service Docker setup
├── 📄 Makefile                    # Common development tasks
├── 📄 main.py                     # FastAPI application entry point
├── 📄 PORT_MANAGEMENT.md          # Port management documentation
│
├── 📁 config/                     # Configuration management
│   ├── __init__.py
│   └── settings.py                # Pydantic settings with env support
│
├── 📁 core/                       # Core business logic
│   ├── __init__.py
│   └── scraper.py                 # Main SwissKnife scraper class
│
├── 📁 api/                        # API layer
│   ├── __init__.py
│   └── routes/                    # API route definitions
│       ├── __init__.py
│       ├── health.py              # Health check endpoints
│       ├── scraping.py            # Main scraping endpoints
│       └── admin.py               # Admin and management endpoints
│
├── 📁 features/                   # Core feature implementations
│   ├── adaptive_extraction.py     # ✅ Intelligent extraction strategies
│   ├── local_llm_integration.py   # ✅ Ollama LLM integration
│   ├── natural_language_interface.py  # 🔄 NLP query processing
│   ├── proxy_rotation.py          # 🔄 Advanced proxy management
│   └── multimodal_processing.py   # 🔄 Multi-content processing
│
├── 📁 models/                     # Data models and schemas
│   ├── __init__.py
│   └── schemas.py                 # Pydantic models for API
│
├── 📁 services/                   # Business services
│   └── __init__.py
│
├── 📁 utils/                      # Utility functions
│   ├── __init__.py
│   ├── exceptions.py              # Custom exceptions and handlers
│   ├── logging.py                 # Logging configuration
│   └── port_manager.py            # Port management utilities
│
├── 📁 tests/                      # Test suite
│   ├── __init__.py
│   └── test_main.py               # Basic application tests
│
├── 📁 scripts/                    # Utility scripts
│   ├── start.py                   # Application startup script
│   └── port_check.py              # Port management script
│
├── 📁 swiss_knife/                # Legacy directory (to be integrated)
│   └── day_one_core.py
│
└── 📁 Docs/                       # Documentation
    ├── PRD.md                     # Product Requirements Document
    ├── tech_stack.md              # Technology stack overview
    ├── Features.md
    ├── Smart_Scraper_AI.md
    ├── crawl4ai_custom_context.md
    ├── jin.md
    ├── project_structure.md       # This file
    └── project_status.md          # Development status log
```

## 🏗️ Architecture Overview

### Core Components

1. **FastAPI Application (`main.py`)**
   - Application entry point and lifecycle management
   - Middleware configuration (CORS, error handling)
   - Route registration and dependency injection

2. **Configuration Management (`config/`)**
   - Environment-based settings with Pydantic
   - Feature flags and service configuration
   - Automatic directory creation

3. **Core Scraper (`core/scraper.py`)**
   - Main orchestration class
   - Component initialization and management
   - Session handling and state tracking

4. **Feature Implementations (`features/`)**
   - **Adaptive Extraction**: ✅ Intelligent strategy selection with CSS, XPath, Regex, and LLM fallbacks
   - **Local LLM Integration**: ✅ Complete Ollama integration with model management
   - **Natural Language Interface**: 🔄 Needs implementation
   - **Proxy Rotation**: 🔄 Needs implementation  
   - **Multimodal Processing**: 🔄 Needs implementation

5. **API Layer (`api/routes/`)**
   - RESTful endpoints for all functionality
   - Request/response models with validation
   - Error handling and status reporting

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Ollama (for local LLM)

### Quick Start
```bash
# 1. Clone and setup
git clone <repository>
cd scrapeagent

# 2. Setup environment
make setup

# 3. Start services
make docker-up

# 4. Start application
make start
```

### Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your configuration

# 3. Install Ollama models
ollama pull mistral
ollama pull llama3.2

# 4. Start application
python scripts/start.py
```

## 🔧 Development

### Available Commands
```bash
make help          # Show all available commands
make install       # Install dependencies
make dev           # Setup development environment
make start         # Start application on port 8601
make restart-clean # Clean restart (kill old processes)
make test          # Run tests
make lint          # Run code linting
make format        # Format code
make check-port    # Check port 8601 status
make kill-port     # Kill processes on port 8601
make docker-up     # Start with Docker
```

### Testing
```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test
pytest tests/test_main.py -v
```

## 📊 Current Implementation Status

### ✅ Completed
- [x] Project structure and configuration
- [x] FastAPI application with proper middleware
- [x] Configuration management with environment variables
- [x] Docker and Docker Compose setup
- [x] Adaptive extraction engine with multiple strategies
- [x] Local LLM integration with Ollama
- [x] API endpoints for health checks and basic scraping
- [x] Error handling and logging system
- [x] Port management system with automatic conflict resolution
- [x] Basic test structure
- [x] Development tooling (Makefile, startup scripts)

### 🔄 In Progress / TODO
- [ ] Complete natural language interface implementation
- [ ] Advanced proxy rotation system
- [ ] Multimodal content processing (images, PDFs, etc.)
- [ ] Database integration (Supabase/PostgreSQL)
- [ ] Session management and user authentication
- [ ] Batch processing and job queues
- [ ] Monitoring and metrics (Prometheus/Grafana)
- [ ] Comprehensive test suite
- [ ] Documentation and tutorials

### 🎯 Next Steps
1. **Complete Core Features**: Finish implementing the remaining feature modules
2. **Database Integration**: Set up Supabase or PostgreSQL for data persistence
3. **Enhanced Testing**: Add comprehensive unit and integration tests
4. **Performance Optimization**: Implement caching and optimize extraction strategies
5. **User Interface**: Build a web interface for easier interaction
6. **Documentation**: Create comprehensive API documentation and user guides

## 🔗 Key Endpoints

Once running, the application provides:

- **API Documentation**: http://localhost:8601/docs
- **Health Check**: http://localhost:8601/health
- **Basic Scraping**: POST http://localhost:8601/api/v1/scrape/
- **Natural Language**: POST http://localhost:8601/api/v1/scrape/natural-language
- **Admin Panel**: http://localhost:8601/api/v1/admin/status
- **Port Management**: GET http://localhost:8601/api/v1/admin/port/status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Format code: `make format`
6. Submit a pull request

## 📝 Notes

- The project uses modern Python practices with Pydantic, FastAPI, and async/await
- All AI processing happens locally using Ollama for privacy
- The architecture is designed for scalability and modularity
- Docker support enables easy deployment and development
- Port 8601 is permanently assigned with automatic conflict resolution
