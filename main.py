"""
SwissKnife AI Scraper - Main Application Entry Point
The Ultimate Web Scraping Swiss Knife with Local AI Intelligence
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config.settings import get_settings
from core.scraper import SwissKnifeScraper
from api.routes import scraping, health, admin
from utils.logging import setup_logging
from utils.exceptions import setup_exception_handlers
from utils.port_manager import check_and_prepare_port


# Global application state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    settings = get_settings()
    
    # Setup logging
    setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting SwissKnife AI Scraper...")
    
    try:
        # Initialize core scraper
        scraper = SwissKnifeScraper()
        await scraper.initialize()
        app_state["scraper"] = scraper
        
        logger.info("✅ SwissKnife AI Scraper initialized successfully")
        logger.info(f"🌐 Server running on {settings.HOST}:{settings.PORT}")
        logger.info(f"📚 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    finally:
        # Cleanup
        logger.info("🛑 Shutting down SwissKnife AI Scraper...")
        if "scraper" in app_state:
            await app_state["scraper"].cleanup()
        logger.info("✅ Cleanup completed")


# Create FastAPI application
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="The Ultimate Web Scraping Swiss Knife with Local AI Intelligence",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add middleware
    if settings.ENABLE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"]
    )
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(scraping.router, prefix="/api/v1/scrape", tags=["Scraping"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
    
    return app


# Create app instance
app = create_app()


# Dependency to get scraper instance
async def get_scraper() -> SwissKnifeScraper:
    """Get the initialized scraper instance"""
    if "scraper" not in app_state:
        raise HTTPException(status_code=503, detail="Scraper not initialized")
    return app_state["scraper"]


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with application information"""
    settings = get_settings()
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "The Ultimate Web Scraping Swiss Knife with Local AI Intelligence",
        "status": "running",
        "features": {
            "adaptive_extraction": settings.ENABLE_ADAPTIVE_EXTRACTION,
            "natural_language_interface": settings.ENABLE_NATURAL_LANGUAGE_INTERFACE,
            "multimodal_processing": settings.ENABLE_MULTIMODAL_PROCESSING,
            "proxy_rotation": settings.ENABLE_PROXY_ROTATION,
            "content_intelligence": settings.ENABLE_CONTENT_INTELLIGENCE,
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "scraping": "/api/v1/scrape",
            "admin": "/api/v1/admin"
        }
    }


@app.get("/status", response_model=Dict[str, Any])
async def status(scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Get detailed application status"""
    try:
        scraper_status = await scraper.get_status()
        return {
            "application": "healthy",
            "scraper": scraper_status,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "application": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
        )


if __name__ == "__main__":
    settings = get_settings()

    # Ensure port is available before starting
    if not check_and_prepare_port():
        print(f"❌ Failed to secure port {settings.PORT}")
        exit(1)

    print(f"🚀 Starting SwissKnife AI Scraper on port {settings.PORT}")

    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG and settings.RELOAD_ON_CHANGE,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
