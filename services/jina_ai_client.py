"""
Jina AI Client Service - Core AI Processing Integration
Handles all communication with Jina AI APIs (Reader, Search, Embeddings, Reranker)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

from config.settings import get_settings
from utils.exceptions import ScrapingError


class JinaAIClient:
    """
    Dedicated client for Jina AI services integration
    Provides high-level interface to all Jina AI APIs
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.JINA_API_KEY
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Jina AI endpoints
        self.reader_endpoint = self.settings.JINA_READER_ENDPOINT
        self.search_endpoint = self.settings.JINA_SEARCH_ENDPOINT
        self.embeddings_endpoint = self.settings.JINA_EMBEDDINGS_ENDPOINT
        self.reranker_endpoint = self.settings.JINA_RERANKER_ENDPOINT
        
        if not self.api_key:
            self.logger.warning("⚠️ Jina AI API key not configured - some features may be limited")
    
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
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
            
            self.logger.info("✅ Jina AI client initialized")
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def read_url(self, url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Use Jina AI Reader API to extract content from URL
        
        Args:
            url: URL to read and extract content from
            options: Optional parameters for the Reader API
            
        Returns:
            Extracted content and metadata
        """
        if not self.session:
            await self.initialize()
        
        try:
            # Build Reader API URL
            reader_url = f"{self.reader_endpoint}/{url}"
            
            # Add query parameters if provided
            params = {}
            if options:
                if options.get("format"):
                    params["format"] = options["format"]
                if options.get("summary"):
                    params["summary"] = "true"
                if options.get("links"):
                    params["links"] = "true"
                if options.get("images"):
                    params["images"] = "true"
            
            self.logger.info(f"🔍 Reading URL via Jina AI Reader: {url}")
            
            async with self.session.get(reader_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    result = {
                        "url": url,
                        "content": content,
                        "success": True,
                        "source": "jina_ai_reader",
                        "timestamp": datetime.now().isoformat(),
                        "status_code": response.status
                    }
                    
                    self.logger.info(f"✅ Jina AI Reader successful for {url}")
                    return result
                else:
                    error_text = await response.text()
                    raise ScrapingError(f"Jina AI Reader API error: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error communicating with Jina AI Reader: {e}")
        except Exception as e:
            raise ScrapingError(f"Unexpected error during Jina AI Reader: {e}")
    
    async def search(self, query: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Use Jina AI Search API to search the web
        
        Args:
            query: Search query
            options: Optional parameters for the Search API
            
        Returns:
            Search results and metadata
        """
        if not self.session:
            await self.initialize()
        
        try:
            # Build Search API URL
            search_url = f"{self.search_endpoint}/{query}"
            
            # Add query parameters if provided
            params = {}
            if options:
                if options.get("count"):
                    params["count"] = options["count"]
                if options.get("format"):
                    params["format"] = options["format"]
            
            self.logger.info(f"🔍 Searching via Jina AI Search: {query}")
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    result = {
                        "query": query,
                        "results": content,
                        "success": True,
                        "source": "jina_ai_search",
                        "timestamp": datetime.now().isoformat(),
                        "status_code": response.status
                    }
                    
                    self.logger.info(f"✅ Jina AI Search successful for: {query}")
                    return result
                else:
                    error_text = await response.text()
                    raise ScrapingError(f"Jina AI Search API error: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error communicating with Jina AI Search: {e}")
        except Exception as e:
            raise ScrapingError(f"Unexpected error during Jina AI Search: {e}")
    
    async def get_embeddings(self, texts: Union[str, List[str]], model: str = "jina-embeddings-v2-base-en") -> Dict[str, Any]:
        """
        Get embeddings using Jina AI Embeddings API
        
        Args:
            texts: Text or list of texts to embed
            model: Embedding model to use
            
        Returns:
            Embeddings and metadata
        """
        if not self.api_key:
            raise ScrapingError("Jina AI API key required for embeddings")
        
        if not self.session:
            await self.initialize()
        
        try:
            # Prepare request payload
            if isinstance(texts, str):
                texts = [texts]
            
            payload = {
                "model": model,
                "input": texts
            }
            
            self.logger.info(f"🔍 Getting embeddings for {len(texts)} texts via Jina AI")
            
            async with self.session.post(
                self.embeddings_endpoint,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    processed_result = {
                        "embeddings": result.get("data", []),
                        "model": model,
                        "usage": result.get("usage", {}),
                        "success": True,
                        "source": "jina_ai_embeddings",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    self.logger.info(f"✅ Jina AI Embeddings successful for {len(texts)} texts")
                    return processed_result
                else:
                    error_text = await response.text()
                    raise ScrapingError(f"Jina AI Embeddings API error: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error communicating with Jina AI Embeddings: {e}")
        except Exception as e:
            raise ScrapingError(f"Unexpected error during Jina AI Embeddings: {e}")
    
    async def rerank(self, query: str, documents: List[str], model: str = "jina-reranker-v1-base-en") -> Dict[str, Any]:
        """
        Rerank documents using Jina AI Reranker API
        
        Args:
            query: Query to rank documents against
            documents: List of documents to rerank
            model: Reranker model to use
            
        Returns:
            Reranked documents with scores
        """
        if not self.api_key:
            raise ScrapingError("Jina AI API key required for reranking")
        
        if not self.session:
            await self.initialize()
        
        try:
            # Prepare request payload
            payload = {
                "model": model,
                "query": query,
                "documents": documents
            }
            
            self.logger.info(f"🔍 Reranking {len(documents)} documents via Jina AI")
            
            async with self.session.post(
                self.reranker_endpoint,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    processed_result = {
                        "results": result.get("results", []),
                        "model": model,
                        "usage": result.get("usage", {}),
                        "success": True,
                        "source": "jina_ai_reranker",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    self.logger.info(f"✅ Jina AI Reranker successful for {len(documents)} documents")
                    return processed_result
                else:
                    error_text = await response.text()
                    raise ScrapingError(f"Jina AI Reranker API error: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise ScrapingError(f"Network error communicating with Jina AI Reranker: {e}")
        except Exception as e:
            raise ScrapingError(f"Unexpected error during Jina AI Reranker: {e}")
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get Jina AI services status"""
        status = {
            "api_key_configured": bool(self.api_key),
            "endpoints": {
                "reader": self.reader_endpoint,
                "search": self.search_endpoint,
                "embeddings": self.embeddings_endpoint,
                "reranker": self.reranker_endpoint
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Test Reader API (doesn't require API key)
        try:
            test_result = await self.read_url("https://example.com")
            status["reader_status"] = "healthy" if test_result.get("success") else "error"
        except Exception as e:
            status["reader_status"] = f"error: {e}"
        
        return status


# Convenience function for quick access
async def get_jina_ai_client() -> JinaAIClient:
    """Get a configured Jina AI client"""
    client = JinaAIClient()
    await client.initialize()
    return client
