"""
crawl4ai Docker Client Service - Core Integration Layer
Handles all communication with the crawl4ai Docker service on port 11235
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

from config.settings import get_settings
from utils.exceptions import ScrapingError


class Crawl4aiDockerClient:
    """
    Dedicated client for crawl4ai Docker service integration
    Provides high-level interface to crawl4ai REST API
    """
    
    def __init__(self, base_url: Optional[str] = None):
        self.settings = get_settings()
        self.base_url = base_url or self.settings.CRAWL4AI_ENDPOINT
        self.timeout = self.settings.CRAWL4AI_TIMEOUT
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def initialize(self):
        """Initialize the client session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Verify service health
            await self._health_check()
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _health_check(self) -> bool:
        """Check if crawl4ai service is healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    self.logger.info(f"✅ crawl4ai service healthy: {health_data.get('version')}")
                    return True
                else:
                    raise ScrapingError(f"crawl4ai service unhealthy: HTTP {response.status}")
        except Exception as e:
            raise ScrapingError(f"Failed to connect to crawl4ai service: {e}")
    
    async def crawl_url(
        self,
        url: str,
        extraction_strategy: Optional[Dict[str, Any]] = None,
        browser_config: Optional[Dict[str, Any]] = None,
        crawler_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crawl a single URL using crawl4ai Docker service
        
        Args:
            url: URL to crawl
            extraction_strategy: Optional extraction strategy configuration
            browser_config: Optional browser configuration
            crawler_config: Optional crawler configuration
            
        Returns:
            Crawl result with content, metadata, and extracted data
        """
        if not self.session:
            await self.initialize()
        
        # Build request payload
        payload = {
            "urls": [url],
            "crawler_config": self._build_crawler_config(crawler_config),
            "browser_config": self._build_browser_config(browser_config)
        }
        
        # Add extraction strategy if provided
        if extraction_strategy:
            payload["extraction_strategy"] = extraction_strategy
        
        try:
            self.logger.info(f"🔍 Crawling URL via crawl4ai Docker: {url}")
            
            async with self.session.post(
                f"{self.base_url}/crawl",
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return self._process_crawl_result(result, url)
                else:
                    error_text = await response.text()
                    raise ScrapingError(f"crawl4ai API error: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error communicating with crawl4ai: {e}")
        except Exception as e:
            raise ScrapingError(f"Unexpected error during crawl: {e}")
    
    async def crawl_multiple_urls(
        self,
        urls: List[str],
        extraction_strategy: Optional[Dict[str, Any]] = None,
        browser_config: Optional[Dict[str, Any]] = None,
        crawler_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Crawl multiple URLs using crawl4ai Docker service
        
        Args:
            urls: List of URLs to crawl
            extraction_strategy: Optional extraction strategy configuration
            browser_config: Optional browser configuration
            crawler_config: Optional crawler configuration
            
        Returns:
            List of crawl results
        """
        if not self.session:
            await self.initialize()
        
        # Build request payload
        payload = {
            "urls": urls,
            "crawler_config": self._build_crawler_config(crawler_config),
            "browser_config": self._build_browser_config(browser_config)
        }
        
        # Add extraction strategy if provided
        if extraction_strategy:
            payload["extraction_strategy"] = extraction_strategy
        
        try:
            self.logger.info(f"🔍 Crawling {len(urls)} URLs via crawl4ai Docker")
            
            async with self.session.post(
                f"{self.base_url}/crawl",
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return self._process_multiple_crawl_results(result, urls)
                else:
                    error_text = await response.text()
                    raise ScrapingError(f"crawl4ai API error: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error communicating with crawl4ai: {e}")
        except Exception as e:
            raise ScrapingError(f"Unexpected error during multi-crawl: {e}")
    
    async def extract_with_css(self, url: str, css_selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data using CSS selectors via crawl4ai"""
        extraction_strategy = {
            "type": "css",
            "selectors": css_selectors
        }
        
        return await self.crawl_url(url, extraction_strategy=extraction_strategy)
    
    async def extract_with_xpath(self, url: str, xpath_expressions: Dict[str, str]) -> Dict[str, Any]:
        """Extract data using XPath expressions via crawl4ai"""
        extraction_strategy = {
            "type": "xpath",
            "expressions": xpath_expressions
        }
        
        return await self.crawl_url(url, extraction_strategy=extraction_strategy)
    
    async def extract_with_llm(self, url: str, query: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract data using LLM-based extraction via crawl4ai"""
        extraction_strategy = {
            "type": "llm",
            "query": query
        }
        
        if schema:
            extraction_strategy["schema"] = schema
        
        return await self.crawl_url(url, extraction_strategy=extraction_strategy)
    
    def _build_crawler_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build crawler configuration with defaults"""
        default_config = {
            "headless": True,
            "cache_mode": "BYPASS",
            "timeout": self.timeout,
            "wait_for_images": False,
            "screenshot": False
        }
        
        if config:
            default_config.update(config)
        
        return default_config
    
    def _build_browser_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build browser configuration with defaults"""
        default_config = {
            "browser_type": "chromium",
            "user_agent": self.settings.DEFAULT_USER_AGENT,
            "viewport": {"width": 1920, "height": 1080}
        }
        
        if config:
            default_config.update(config)
        
        return default_config
    
    def _process_crawl_result(self, result: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Process single crawl result from crawl4ai API"""
        if "results" not in result or not result["results"]:
            raise ScrapingError(f"No results returned for URL: {url}")
        
        crawl_result = result["results"][0]
        
        # Standardize the result format
        processed_result = {
            "url": crawl_result.get("url", url),
            "success": crawl_result.get("success", False),
            "status_code": crawl_result.get("status_code"),
            "html": crawl_result.get("html", ""),
            "markdown": crawl_result.get("markdown", ""),
            "extracted_content": crawl_result.get("extracted_content"),
            "metadata": crawl_result.get("metadata", {}),
            "links": crawl_result.get("links", []),
            "images": crawl_result.get("images", []),
            "tables": crawl_result.get("tables", []),
            "processing_time": crawl_result.get("processing_time", 0),
            "timestamp": datetime.now().isoformat(),
            "source": "crawl4ai_docker"
        }
        
        if not processed_result["success"]:
            error_msg = crawl_result.get("error_message", "Unknown crawl error")
            self.logger.warning(f"⚠️ crawl4ai crawl failed for {url}: {error_msg}")
            processed_result["error_message"] = error_msg
        else:
            self.logger.info(f"✅ crawl4ai crawl successful for {url}")
        
        return processed_result
    
    def _process_multiple_crawl_results(self, result: Dict[str, Any], urls: List[str]) -> List[Dict[str, Any]]:
        """Process multiple crawl results from crawl4ai API"""
        if "results" not in result:
            raise ScrapingError("No results returned from crawl4ai API")
        
        processed_results = []
        for i, crawl_result in enumerate(result["results"]):
            url = urls[i] if i < len(urls) else crawl_result.get("url", "unknown")
            processed_result = self._process_crawl_result({"results": [crawl_result]}, url)
            processed_results.append(processed_result)
        
        return processed_results
    
    async def get_service_info(self) -> Dict[str, Any]:
        """Get crawl4ai service information"""
        if not self.session:
            await self.initialize()
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise ScrapingError(f"Failed to get service info: HTTP {response.status}")
        except Exception as e:
            raise ScrapingError(f"Error getting service info: {e}")


# Convenience function for quick access
async def get_crawl4ai_client() -> Crawl4aiDockerClient:
    """Get a configured crawl4ai Docker client"""
    client = Crawl4aiDockerClient()
    await client.initialize()
    return client
