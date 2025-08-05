"""
Custom exceptions and error handling utilities
"""

from typing import Any, Dict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging


class SwissKnifeException(Exception):
    """Base exception for SwissKnife AI Scraper"""
    pass


class InitializationError(SwissKnifeException):
    """Raised when component initialization fails"""
    pass


class ScrapingError(SwissKnifeException):
    """Raised when scraping operations fail"""
    pass


class ProxyError(SwissKnifeException):
    """Raised when proxy operations fail"""
    pass


class LLMError(SwissKnifeException):
    """Raised when LLM operations fail"""
    pass


class ConfigurationError(SwissKnifeException):
    """Raised when configuration is invalid"""
    pass


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers for the FastAPI app"""
    
    @app.exception_handler(SwissKnifeException)
    async def swissknife_exception_handler(request: Request, exc: SwissKnifeException):
        """Handle custom SwissKnife exceptions"""
        logger = logging.getLogger(__name__)
        logger.error(f"SwissKnife error: {exc}")
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "SwissKnife Error",
                "message": str(exc),
                "type": exc.__class__.__name__
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger = logging.getLogger(__name__)
        logger.warning(f"Validation error: {exc}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "type": exc.__class__.__name__
            }
        )
