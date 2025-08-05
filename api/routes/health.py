"""
Health check and monitoring endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from datetime import datetime

from core.scraper import SwissKnifeScraper
from main import get_scraper

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "SwissKnife AI Scraper"
    }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Detailed health check with component status"""
    try:
        scraper_status = await scraper.get_status()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "SwissKnife AI Scraper",
            "scraper": scraper_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "SwissKnife AI Scraper",
            "error": str(e)
        }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Readiness check for Kubernetes/Docker"""
    try:
        if scraper.is_initialized:
            return {
                "status": "ready",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "not_ready",
                "timestamp": datetime.now().isoformat(),
                "reason": "Scraper not initialized"
            }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.get("/live", response_model=Dict[str, Any])
async def liveness_check():
    """Liveness check for Kubernetes/Docker"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }
