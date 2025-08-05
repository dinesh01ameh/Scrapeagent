"""
Admin and management endpoints
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.scraper import SwissKnifeScraper
from config.settings import get_settings
from utils.port_manager import get_port_info, PortManager

router = APIRouter()


# Dependency to get scraper instance
async def get_scraper() -> SwissKnifeScraper:
    """Get the initialized scraper instance"""
    # Import here to avoid circular imports
    from main import app_state
    if "scraper" not in app_state:
        raise HTTPException(status_code=503, detail="Scraper not initialized")
    return app_state["scraper"]


class ProxyConfig(BaseModel):
    """Proxy configuration model"""
    proxy_list: List[str]
    pool_type: str = "datacenter"


@router.get("/status", response_model=Dict[str, Any])
async def get_admin_status(scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Get detailed system status for admin dashboard"""
    try:
        status = await scraper.get_status()
        settings = get_settings()
        
        return {
            "system": {
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "debug_mode": settings.DEBUG,
                "features": {
                    "adaptive_extraction": settings.ENABLE_ADAPTIVE_EXTRACTION,
                    "natural_language": settings.ENABLE_NATURAL_LANGUAGE_INTERFACE,
                    "multimodal": settings.ENABLE_MULTIMODAL_PROCESSING,
                    "proxy_rotation": settings.ENABLE_PROXY_ROTATION,
                    "content_intelligence": settings.ENABLE_CONTENT_INTELLIGENCE,
                }
            },
            "scraper": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=Dict[str, Any])
async def get_configuration():
    """Get current configuration (non-sensitive values only)"""
    settings = get_settings()
    
    return {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
            "host": settings.HOST,
            "port": settings.PORT,
        },
        "features": {
            "adaptive_extraction": settings.ENABLE_ADAPTIVE_EXTRACTION,
            "natural_language": settings.ENABLE_NATURAL_LANGUAGE_INTERFACE,
            "multimodal": settings.ENABLE_MULTIMODAL_PROCESSING,
            "proxy_rotation": settings.ENABLE_PROXY_ROTATION,
            "content_intelligence": settings.ENABLE_CONTENT_INTELLIGENCE,
        },
        "limits": {
            "max_concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
            "max_content_size": settings.MAX_CONTENT_SIZE,
            "max_pages_per_domain": settings.MAX_PAGES_PER_DOMAIN,
            "rate_limit_per_minute": settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        }
    }


@router.post("/proxies", response_model=Dict[str, Any])
async def add_proxy_pool(
    config: ProxyConfig,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """Add a new proxy pool"""
    try:
        if not scraper.proxy_manager:
            raise HTTPException(status_code=400, detail="Proxy rotation not enabled")
        
        await scraper.proxy_manager.add_proxy_pool(
            config.proxy_list,
            config.pool_type
        )
        
        return {
            "success": True,
            "message": f"Added {len(config.proxy_list)} proxies to {config.pool_type} pool"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proxies/status", response_model=Dict[str, Any])
async def get_proxy_status(scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Get proxy pool status and health"""
    try:
        if not scraper.proxy_manager:
            raise HTTPException(status_code=400, detail="Proxy rotation not enabled")
        
        status = await scraper.proxy_manager.get_status()
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=Dict[str, Any])
async def get_llm_models(scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Get available LLM models and their status"""
    try:
        if not scraper.llm_manager:
            raise HTTPException(status_code=400, detail="LLM integration not enabled")
        
        models = await scraper.llm_manager.get_available_models()
        return {
            "available_models": models,
            "default_model": get_settings().DEFAULT_MODEL,
            "fallback_model": get_settings().FALLBACK_MODEL,
            "code_model": get_settings().CODE_MODEL,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_name}/warm-up", response_model=Dict[str, Any])
async def warm_up_model(
    model_name: str,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """Warm up a specific LLM model"""
    try:
        if not scraper.llm_manager:
            raise HTTPException(status_code=400, detail="LLM integration not enabled")
        
        await scraper.llm_manager.warm_up_model(model_name)
        return {
            "success": True,
            "message": f"Model {model_name} warmed up successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """Get system metrics (placeholder)"""
    # In a full implementation, this would return Prometheus metrics
    return {
        "message": "Metrics endpoint not yet implemented",
        "suggestion": "Use Prometheus endpoint on port 9090 when implemented"
    }


@router.get("/port/status", response_model=Dict[str, Any])
async def get_port_status():
    """Get current port status and information"""
    try:
        settings = get_settings()
        port_info = get_port_info(settings.PORT)

        return {
            "success": True,
            "port_info": port_info,
            "configured_port": settings.PORT,
            "message": f"Port {settings.PORT} is {'available' if port_info['available'] else 'busy'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/port/cleanup", response_model=Dict[str, Any])
async def cleanup_port_conflicts():
    """Clean up any processes conflicting with our port"""
    try:
        settings = get_settings()
        port_manager = PortManager(settings.PORT)

        # Clean up old processes
        cleaned = port_manager.cleanup_old_processes()

        # Ensure port is available
        port_secured = port_manager.ensure_port_available(settings.PORT, force=True)

        return {
            "success": port_secured,
            "cleaned_processes": cleaned,
            "port": settings.PORT,
            "message": f"Port {settings.PORT} cleanup {'successful' if port_secured else 'failed'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart", response_model=Dict[str, Any])
async def restart_server():
    """Restart the server (placeholder - requires process management)"""
    try:
        settings = get_settings()

        # In a production environment, this would trigger a graceful restart
        # For now, we'll just return information about how to restart
        return {
            "message": "Server restart requested",
            "port": settings.PORT,
            "instructions": [
                "To restart the server:",
                "1. Stop the current process (Ctrl+C)",
                "2. Run: python scripts/start.py",
                "3. Or use: make start"
            ],
            "note": "Automatic restart not implemented in development mode"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Proxy Management Endpoints

@router.post("/proxy/add", response_model=Dict[str, Any])
async def add_proxy_pool(
    proxy_config: ProxyConfig,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """Add a pool of proxies"""
    try:
        if not scraper.proxy_manager:
            raise HTTPException(status_code=400, detail="Proxy rotation not enabled")

        validated_count = await scraper.proxy_manager.add_proxy_pool(
            proxy_config.proxy_list,
            proxy_config.pool_type
        )

        return {
            "message": f"Added {validated_count}/{len(proxy_config.proxy_list)} proxies to {proxy_config.pool_type} pool",
            "validated_count": validated_count,
            "total_submitted": len(proxy_config.proxy_list),
            "pool_type": proxy_config.pool_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proxy/statistics", response_model=Dict[str, Any])
async def get_proxy_statistics(scraper: SwissKnifeScraper = Depends(get_scraper)):
    """Get comprehensive proxy statistics"""
    try:
        if not scraper.proxy_manager:
            raise HTTPException(status_code=400, detail="Proxy rotation not enabled")

        return scraper.proxy_manager.get_proxy_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proxy/details", response_model=Dict[str, Any])
async def get_proxy_details(
    proxy_id: str = None,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """Get detailed proxy information"""
    try:
        if not scraper.proxy_manager:
            raise HTTPException(status_code=400, detail="Proxy rotation not enabled")

        return scraper.proxy_manager.get_proxy_details(proxy_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proxy/best", response_model=Dict[str, Any])
async def get_best_proxies(
    count: int = 5,
    pool_type: str = None,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """Get best performing proxies"""
    try:
        if not scraper.proxy_manager:
            raise HTTPException(status_code=400, detail="Proxy rotation not enabled")

        best_proxies = scraper.proxy_manager.get_best_proxies(count, pool_type)

        return {
            "best_proxies": [
                {
                    "proxy_id": proxy["proxy_id"],
                    "pool_type": proxy["pool_type"],
                    "geographic_location": proxy.get("geographic_location"),
                    "health_score": scraper.proxy_manager.proxy_metrics.get(proxy["proxy_id"]).health_score
                    if scraper.proxy_manager.proxy_metrics.get(proxy["proxy_id"]) else 1.0
                }
                for proxy in best_proxies
            ],
            "count": len(best_proxies),
            "requested_count": count,
            "pool_type": pool_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/proxy/{proxy_id}", response_model=Dict[str, Any])
async def remove_proxy(
    proxy_id: str,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """Remove a specific proxy"""
    try:
        if not scraper.proxy_manager:
            raise HTTPException(status_code=400, detail="Proxy rotation not enabled")

        success = await scraper.proxy_manager.remove_proxy(proxy_id)

        if success:
            return {"message": f"Proxy {proxy_id} removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Proxy not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/proxy/pool/{pool_type}", response_model=Dict[str, Any])
async def clear_proxy_pool(
    pool_type: str,
    scraper: SwissKnifeScraper = Depends(get_scraper)
):
    """Clear all proxies from a specific pool"""
    try:
        if not scraper.proxy_manager:
            raise HTTPException(status_code=400, detail="Proxy rotation not enabled")

        cleared_count = await scraper.proxy_manager.clear_pool(pool_type)

        return {
            "message": f"Cleared {cleared_count} proxies from {pool_type} pool",
            "cleared_count": cleared_count,
            "pool_type": pool_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
