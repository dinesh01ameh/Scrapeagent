"""
Performance Optimization Service for Smart Scraper AI
Optimizes crawl4ai Docker + Jina AI integration for maximum efficiency
"""

import asyncio
import time
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque

# Optional Redis dependency
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

from config.settings import get_settings
from utils.logging import LoggingMixin


@dataclass
class PerformanceMetrics:
    """Performance metrics for the integrated stack"""
    crawl4ai_avg_response_time: float = 0.0
    jina_ai_avg_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    memory_usage_mb: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    timestamp: str = ""


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_accessed: float = 0.0


class SmartScraperOptimizer(LoggingMixin):
    """
    Optimizes the integrated crawl4ai + Jina AI stack for maximum performance
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        super().__init__()
        self.settings = get_settings()
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_client = None
        
        # Performance metrics
        self.metrics = PerformanceMetrics()
        self.response_times = {
            'crawl4ai': deque(maxlen=100),
            'jina_ai': deque(maxlen=100)
        }
        
        # In-memory cache for fast access
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.max_memory_cache_size = 1000
        
        # Rate limiting configuration
        self.rate_limits = {
            'crawl4ai': {
                'rpm': 300,  # Requests per minute
                'current': 0,
                'window_start': time.time(),
                'burst_limit': 50  # Burst capacity
            },
            'jina_reader': {
                'rpm': 200,
                'current': 0,
                'window_start': time.time(),
                'burst_limit': 20
            },
            'jina_search': {
                'rpm': 40,
                'current': 0,
                'window_start': time.time(),
                'burst_limit': 10
            },
            'jina_embeddings': {
                'rpm': 100,
                'current': 0,
                'window_start': time.time(),
                'burst_limit': 15
            }
        }
        
        # Performance optimization settings
        self.optimization_config = {
            'cache_ttl': {
                'crawl4ai_basic': 3600,  # 1 hour
                'crawl4ai_css': 1800,    # 30 minutes
                'crawl4ai_llm': 900,     # 15 minutes
                'jina_reader': 7200,     # 2 hours
                'jina_search': 1800,     # 30 minutes
                'jina_embeddings': 86400 # 24 hours
            },
            'retry_config': {
                'max_retries': 3,
                'backoff_factor': 1.5,
                'retry_statuses': [429, 500, 502, 503, 504]
            }
        }
    
    async def initialize(self):
        """Initialize the performance optimizer"""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = aioredis.from_url(self.redis_url)
                await self.redis_client.ping()
                self.logger.info("✅ Redis cache connected for performance optimization")
            except Exception as e:
                self.logger.warning(f"⚠️ Redis not available, using memory cache only: {e}")
                self.redis_client = None
        else:
            self.logger.info("⚠️ Redis not installed, using memory cache only")
            self.redis_client = None
    
    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    def _generate_cache_key(self, service: str, method: str, params: Dict[str, Any]) -> str:
        """Generate a unique cache key"""
        key_data = {
            'service': service,
            'method': method,
            'params': params
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"scraper_cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get result from cache (Redis or memory)"""
        try:
            # Check memory cache first
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if time.time() - entry.timestamp < entry.ttl:
                    entry.access_count += 1
                    entry.last_accessed = time.time()
                    return entry.data
                else:
                    del self.memory_cache[cache_key]
            
            # Check Redis cache
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            
            return None
        except Exception as e:
            self.logger.warning(f"Cache retrieval error: {e}")
            return None
    
    async def set_cached_result(self, cache_key: str, data: Any, ttl: int):
        """Set result in cache (Redis and memory)"""
        try:
            # Store in memory cache
            if len(self.memory_cache) >= self.max_memory_cache_size:
                # Remove least recently used item
                lru_key = min(self.memory_cache.keys(), 
                            key=lambda k: self.memory_cache[k].last_accessed)
                del self.memory_cache[lru_key]
            
            self.memory_cache[cache_key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=ttl,
                last_accessed=time.time()
            )
            
            # Store in Redis cache
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key, 
                    ttl, 
                    json.dumps(data, default=str)
                )
        except Exception as e:
            self.logger.warning(f"Cache storage error: {e}")
    
    async def check_rate_limit(self, service: str) -> Tuple[bool, float]:
        """Check if request is within rate limits"""
        now = time.time()
        limits = self.rate_limits.get(service, {})
        
        if not limits:
            return True, 0.0
        
        # Reset window if needed
        if now - limits['window_start'] >= 60:  # 1 minute window
            limits['current'] = 0
            limits['window_start'] = now
        
        # Check if within limits
        if limits['current'] < limits['rpm']:
            limits['current'] += 1
            return True, 0.0
        
        # Calculate wait time
        wait_time = 60 - (now - limits['window_start'])
        return False, wait_time
    
    async def optimize_crawl4ai_config(self, extraction_type: str = "basic") -> Dict[str, Any]:
        """Generate optimized crawl4ai configuration based on performance metrics"""
        base_config = {
            'headless': True,
            'cache_mode': 'SMART',
            'timeout': 30,
            'wait_for_images': False,
            'screenshot': False,
            'user_agent': self.settings.DEFAULT_USER_AGENT
        }
        
        # Optimize based on extraction type
        if extraction_type == "css":
            base_config.update({
                'timeout': 20,
                'wait_for_selector': True,
                'remove_overlay_elements': True
            })
        elif extraction_type == "llm":
            base_config.update({
                'timeout': 45,
                'extract_text': True,
                'clean_html': True
            })
        elif extraction_type == "xpath":
            base_config.update({
                'timeout': 25,
                'preserve_structure': True
            })
        
        # Adjust based on current performance
        avg_response_time = self.metrics.crawl4ai_avg_response_time
        if avg_response_time > 10:  # Slow responses
            base_config['timeout'] = min(base_config['timeout'] + 10, 60)
        elif avg_response_time < 3:  # Fast responses
            base_config['timeout'] = max(base_config['timeout'] - 5, 15)
        
        return base_config
    
    async def optimize_jina_requests(self, request_type: str) -> Dict[str, Any]:
        """Optimize Jina AI API requests based on rate limits and performance"""
        configs = {
            'reader': {
                'options': {
                    'format': 'markdown',
                    'summary': False,  # Disable for speed unless needed
                    'links': False,
                    'images': False
                },
                'headers': {
                    'X-No-Cache': 'false',
                    'X-Target-Selector': 'main, article, .content, #content',
                    'X-Remove-Selector': 'header, footer, nav, .ads, .sidebar',
                    'X-Timeout': '10'
                }
            },
            'search': {
                'options': {
                    'count': 10,
                    'format': 'json'
                }
            },
            'embeddings': {
                'model': 'jina-embeddings-v2-base-en',
                'batch_size': 32  # Optimize batch size
            },
            'reranker': {
                'model': 'jina-reranker-v1-base-en',
                'top_n': 10
            }
        }
        
        config = configs.get(request_type, {})
        
        # Adjust based on current performance
        avg_response_time = self.metrics.jina_ai_avg_response_time
        if request_type == 'reader' and avg_response_time > 8:
            # Reduce timeout for faster responses
            config['headers']['X-Timeout'] = '8'
            config['options']['summary'] = False
        
        return config
    
    async def intelligent_request_routing(self, url: str, extraction_type: str, query: Optional[str] = None) -> str:
        """Route requests intelligently between crawl4ai and Jina AI based on performance"""
        
        # Check rate limits for both services
        crawl4ai_available, crawl4ai_wait = await self.check_rate_limit('crawl4ai')
        jina_available, jina_wait = await self.check_rate_limit('jina_reader')
        
        # Route based on extraction type and availability
        if extraction_type in ['css', 'xpath', 'text', 'basic']:
            if crawl4ai_available:
                return 'crawl4ai_primary'
            elif jina_available and extraction_type in ['text', 'basic']:
                return 'jina_reader_fallback'
        
        elif extraction_type in ['pdf', 'document', 'multimodal']:
            if jina_available:
                return 'jina_reader_primary'
            elif crawl4ai_available:
                return 'crawl4ai_fallback'
        
        elif extraction_type == 'llm' and query:
            # For LLM extraction, prefer crawl4ai for structured content
            if crawl4ai_available:
                return 'crawl4ai_llm_primary'
            elif jina_available:
                return 'jina_reader_llm_fallback'
        
        # If both services are rate limited, return the one with shorter wait
        if not crawl4ai_available and not jina_available:
            if crawl4ai_wait <= jina_wait:
                return f'crawl4ai_wait_{crawl4ai_wait:.1f}s'
            else:
                return f'jina_wait_{jina_wait:.1f}s'
        
        return 'fallback_strategy'
    
    def record_response_time(self, service: str, response_time: float):
        """Record response time for performance tracking"""
        self.response_times[service].append(response_time)
        
        # Update average response time
        if service == 'crawl4ai':
            self.metrics.crawl4ai_avg_response_time = sum(self.response_times['crawl4ai']) / len(self.response_times['crawl4ai'])
        elif service == 'jina_ai':
            self.metrics.jina_ai_avg_response_time = sum(self.response_times['jina_ai']) / len(self.response_times['jina_ai'])
    
    def record_request_outcome(self, success: bool):
        """Record request outcome for metrics"""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        
        # Update error rate
        if self.metrics.total_requests > 0:
            self.metrics.error_rate = 1 - (self.metrics.successful_requests / self.metrics.total_requests)
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        # Update cache hit rate
        total_cache_requests = len(self.memory_cache)
        if total_cache_requests > 0:
            cache_hits = sum(1 for entry in self.memory_cache.values() if entry.access_count > 0)
            self.metrics.cache_hit_rate = cache_hits / total_cache_requests
        
        # Update timestamp
        self.metrics.timestamp = datetime.now().isoformat()
        
        return self.metrics
    
    async def optimize_performance_settings(self) -> Dict[str, Any]:
        """Generate optimized performance settings based on current metrics"""
        metrics = await self.get_performance_metrics()
        
        optimizations = {
            'cache_strategy': 'aggressive' if metrics.cache_hit_rate < 0.3 else 'balanced',
            'rate_limiting': 'strict' if metrics.error_rate > 0.1 else 'relaxed',
            'timeout_adjustment': 'increase' if metrics.crawl4ai_avg_response_time > 10 else 'maintain',
            'concurrency_level': 'reduce' if metrics.error_rate > 0.05 else 'maintain',
            'recommended_actions': []
        }
        
        # Generate recommendations
        if metrics.cache_hit_rate < 0.2:
            optimizations['recommended_actions'].append('Increase cache TTL values')
        
        if metrics.error_rate > 0.1:
            optimizations['recommended_actions'].append('Implement exponential backoff')
        
        if metrics.crawl4ai_avg_response_time > 15:
            optimizations['recommended_actions'].append('Optimize crawl4ai Docker resources')
        
        return optimizations


# Convenience function for quick access
async def get_performance_optimizer() -> SmartScraperOptimizer:
    """Get a configured performance optimizer"""
    optimizer = SmartScraperOptimizer()
    await optimizer.initialize()
    return optimizer
