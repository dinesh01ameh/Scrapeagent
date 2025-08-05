"""
Services Package - Core Service Layer
Contains service classes for external integrations
"""

from .crawl4ai_client import Crawl4aiDockerClient, get_crawl4ai_client
from .jina_ai_client import JinaAIClient, get_jina_ai_client
from .performance_optimizer import SmartScraperOptimizer, get_performance_optimizer

__all__ = [
    "Crawl4aiDockerClient",
    "get_crawl4ai_client",
    "JinaAIClient",
    "get_jina_ai_client",
    "SmartScraperOptimizer",
    "get_performance_optimizer"
]
