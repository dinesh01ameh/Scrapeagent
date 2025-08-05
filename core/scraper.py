"""
SwissKnife AI Scraper - Core Scraper Implementation
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from config.settings import get_settings
from services.crawl4ai_client import Crawl4aiDockerClient
from services.jina_ai_client import JinaAIClient
from services.performance_optimizer import SmartScraperOptimizer
from features.adaptive_extraction import AdaptiveExtractionEngine
from features.natural_language_interface import NaturalLanguageProcessor
from features.local_llm_integration import LocalLLMManager
from features.proxy_rotation import AdvancedProxyManager
from features.multimodal_processing import MultiModalProcessor
from utils.exceptions import ScrapingError, InitializationError


class SwissKnifeScraper:
    """
    The main SwissKnife AI Scraper class that orchestrates all components
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Core components - PRIORITIZE crawl4ai Docker service and Jina AI
        self.crawl4ai_client: Optional[Crawl4aiDockerClient] = None
        self.jina_ai_client: Optional[JinaAIClient] = None
        self.performance_optimizer: Optional[SmartScraperOptimizer] = None
        self.llm_manager: Optional[LocalLLMManager] = None
        self.extraction_engine: Optional[AdaptiveExtractionEngine] = None
        self.nlp_processor: Optional[NaturalLanguageProcessor] = None
        self.proxy_manager: Optional[AdvancedProxyManager] = None
        self.multimodal_processor: Optional[MultiModalProcessor] = None
        
        # State tracking
        self.is_initialized = False
        self.initialization_time: Optional[datetime] = None
        self.active_sessions: Dict[str, Any] = {}
        
    async def initialize(self):
        """Initialize all scraper components"""
        try:
            self.logger.info("🔧 Initializing SwissKnife AI Scraper components...")

            # CRITICAL: Initialize crawl4ai Docker Client FIRST (Primary Scraping Engine)
            self.logger.info("🚀 Initializing crawl4ai Docker Client (Primary Engine)...")
            self.crawl4ai_client = Crawl4aiDockerClient()
            await self.crawl4ai_client.initialize()
            self.logger.info("✅ crawl4ai Docker Client initialized and ready")

            # CRITICAL: Initialize Jina AI Client SECOND (Core AI Processing Engine)
            self.logger.info("🚀 Initializing Jina AI Client (Core AI Engine)...")
            self.jina_ai_client = JinaAIClient()
            await self.jina_ai_client.initialize()
            self.logger.info("✅ Jina AI Client initialized and ready")

            # CRITICAL: Initialize Performance Optimizer THIRD (Performance Enhancement)
            self.logger.info("⚡ Initializing Performance Optimizer...")
            self.performance_optimizer = SmartScraperOptimizer()
            await self.performance_optimizer.initialize()
            self.logger.info("✅ Performance Optimizer initialized and ready")

            # Initialize Local LLM Manager
            if self.settings.ENABLE_NATURAL_LANGUAGE_INTERFACE or self.settings.ENABLE_CONTENT_INTELLIGENCE:
                self.logger.info("🤖 Initializing Local LLM Manager...")
                self.llm_manager = LocalLLMManager(self.settings.OLLAMA_ENDPOINT)
                await self.llm_manager.initialize()
                self.logger.info("✅ Local LLM Manager initialized")
            
            # Initialize Adaptive Extraction Engine with crawl4ai Docker client
            if self.settings.ENABLE_ADAPTIVE_EXTRACTION:
                self.logger.info("🎯 Initializing Adaptive Extraction Engine...")
                self.extraction_engine = AdaptiveExtractionEngine(
                    local_llm_config={
                        "manager": self.llm_manager,
                        "default_model": self.settings.DEFAULT_MODEL
                    },
                    crawl4ai_client=self.crawl4ai_client  # CRITICAL: Pass crawl4ai client
                )
                self.logger.info("✅ Adaptive Extraction Engine initialized with crawl4ai Docker client")
            
            # Initialize Natural Language Processor
            if self.settings.ENABLE_NATURAL_LANGUAGE_INTERFACE and self.llm_manager:
                self.logger.info("🗣️ Initializing Natural Language Processor...")
                self.nlp_processor = NaturalLanguageProcessor(self.llm_manager)
                self.logger.info("✅ Natural Language Processor initialized")
            
            # Initialize Proxy Manager
            if self.settings.ENABLE_PROXY_ROTATION:
                self.logger.info("🌐 Initializing Advanced Proxy Manager...")
                proxy_config = {
                    "health_check_interval": getattr(self.settings, "PROXY_HEALTH_CHECK_INTERVAL", 300),
                    "max_consecutive_failures": getattr(self.settings, "PROXY_MAX_CONSECUTIVE_FAILURES", 5),
                    "min_health_score": getattr(self.settings, "PROXY_MIN_HEALTH_SCORE", 0.3),
                    "validation_timeout": getattr(self.settings, "PROXY_VALIDATION_TIMEOUT", 10)
                }
                self.proxy_manager = AdvancedProxyManager(proxy_config)
                await self.proxy_manager.initialize()
                self.logger.info("✅ Advanced Proxy Manager initialized")
            
            # Initialize Multi-Modal Processor with Jina AI Client
            if self.settings.ENABLE_MULTIMODAL_PROCESSING and self.llm_manager:
                self.logger.info("📄 Initializing Multi-Modal Processor...")
                jina_config = {
                    "api_key": self.settings.JINA_API_KEY,
                    "endpoint": self.settings.JINA_READER_ENDPOINT
                }
                self.multimodal_processor = MultiModalProcessor(
                    self.llm_manager,
                    jina_config,
                    jina_ai_client=self.jina_ai_client  # CRITICAL: Pass Jina AI client
                )
                self.logger.info("✅ Multi-Modal Processor initialized with Jina AI Client")
            
            self.is_initialized = True
            self.initialization_time = datetime.now()
            self.logger.info("🚀 SwissKnife AI Scraper fully initialized!")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize SwissKnife AI Scraper: {e}")
            raise InitializationError(f"Scraper initialization failed: {e}")
    
    async def scrape(
        self,
        url: str,
        query: Optional[str] = None,
        extraction_config: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main scraping method with intelligent extraction
        """
        if not self.is_initialized:
            raise ScrapingError("Scraper not initialized. Call initialize() first.")
        
        try:
            start_time = time.time()
            self.logger.info(f"🔍 Starting optimized scrape for URL: {url}")

            # PERFORMANCE OPTIMIZATION: Intelligent request routing
            extraction_type = self._determine_extraction_type(extraction_config, query)

            if self.performance_optimizer:
                # Check cache first
                cache_key = self.performance_optimizer._generate_cache_key(
                    "scraper", "scrape", {"url": url, "query": query, "config": extraction_config}
                )
                cached_result = await self.performance_optimizer.get_cached_result(cache_key)
                if cached_result:
                    self.logger.info("⚡ Cache hit - returning cached result")
                    return cached_result

                # Get intelligent routing decision
                routing_decision = await self.performance_optimizer.intelligent_request_routing(
                    url, extraction_type, query
                )
                self.logger.info(f"🎯 Routing decision: {routing_decision}")

                # Handle rate limiting
                if "wait" in routing_decision:
                    wait_time = float(routing_decision.split("_")[-1].replace("s", ""))
                    self.logger.warning(f"⏳ Rate limited, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)

            # PRIORITY 1: Use crawl4ai Docker service (Primary Engine) with optimization
            if self.crawl4ai_client:
                self.logger.info("🚀 Using optimized crawl4ai Docker service (Primary Engine)")

                # Get optimized configuration
                if self.performance_optimizer:
                    crawl4ai_config = await self.performance_optimizer.optimize_crawl4ai_config(extraction_type)
                else:
                    crawl4ai_config = {}

                try:
                    if query and extraction_config:
                        # Use LLM extraction via crawl4ai
                        result = await self.crawl4ai_client.extract_with_llm(url, query)
                    elif extraction_config and extraction_config.get("css_selectors"):
                        # Use CSS extraction via crawl4ai
                        result = await self.crawl4ai_client.extract_with_css(url, extraction_config["css_selectors"])
                    elif extraction_config and extraction_config.get("xpath_expressions"):
                        # Use XPath extraction via crawl4ai
                        result = await self.crawl4ai_client.extract_with_xpath(url, extraction_config["xpath_expressions"])
                    else:
                        # Basic crawl via crawl4ai
                        result = await self.crawl4ai_client.crawl_url(url, crawler_config=crawl4ai_config)

                    # Record performance metrics
                    response_time = time.time() - start_time
                    if self.performance_optimizer:
                        self.performance_optimizer.record_response_time('crawl4ai', response_time)
                        self.performance_optimizer.record_request_outcome(result.get("success", False))

                        # Cache successful results
                        if result.get("success"):
                            ttl = self.performance_optimizer.optimization_config['cache_ttl'].get(f'crawl4ai_{extraction_type}', 3600)
                            await self.performance_optimizer.set_cached_result(cache_key, result, ttl)

                    final_result = {
                        "url": url,
                        "query": query,
                        "result": result,
                        "method": "crawl4ai_docker_primary_optimized",
                        "timestamp": datetime.now().isoformat(),
                        "source": "crawl4ai_docker_service",
                        "response_time": response_time,
                        "extraction_type": extraction_type
                    }

                    return final_result

                except Exception as e:
                    self.logger.warning(f"⚠️ Optimized crawl4ai failed: {e}")
                    # Record failure
                    if self.performance_optimizer:
                        self.performance_optimizer.record_request_outcome(False)

            # FALLBACK 1: Use adaptive extraction if available
            if self.extraction_engine and query:
                self.logger.info("⚠️ Falling back to adaptive extraction engine")
                result = await self.extraction_engine.analyze_and_extract(url, query)
                return {
                    "url": url,
                    "query": query,
                    "result": result,
                    "method": "adaptive_extraction_fallback",
                    "timestamp": datetime.now().isoformat()
                }

            # FALLBACK 2: Basic extraction
            self.logger.warning("⚠️ Using basic extraction fallback")
            return await self._basic_scrape(url, extraction_config)
            
        except Exception as e:
            self.logger.error(f"❌ Scraping failed for {url}: {e}")
            raise ScrapingError(f"Scraping failed: {e}")
    
    async def natural_language_scrape(
        self,
        url: str,
        query: str,
        session_id: Optional[str] = None,
        check_ambiguity: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape using natural language commands
        """
        if not self.nlp_processor:
            raise ScrapingError("Natural Language Interface not enabled")

        try:
            self.logger.info(f"🗣️ Processing natural language query: {query}")

            # Process natural language command
            result = await self.nlp_processor.process_command(query, session_id, check_ambiguity)

            # Check if clarification is needed
            if result.get("requires_clarification", False):
                return {
                    "success": True,
                    "requires_clarification": True,
                    "ambiguity_check": result["ambiguity_check"],
                    "partial_intent": result["partial_intent"],
                    "message": result["message"],
                    "url": url,
                    "query": query,
                    "session_id": session_id
                }

            # Execute scraping with generated config
            extraction_config = result["extraction_config"]
            scrape_result = await self.scrape(url, query, extraction_config, session_id)

            # Add NLP processing metadata
            scrape_result["nlp_metadata"] = {
                "intent": result["intent"],
                "entities": result["entities"],
                "processing_timestamp": datetime.now().isoformat()
            }

            return scrape_result

        except Exception as e:
            self.logger.error(f"❌ Natural language scraping failed: {e}")
            raise ScrapingError(f"Natural language scraping failed: {e}")

    async def resolve_ambiguous_query(
        self,
        url: str,
        original_query: str,
        clarification: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve an ambiguous natural language query with user clarification
        """
        if not self.nlp_processor:
            raise ScrapingError("Natural Language Interface not enabled")

        try:
            self.logger.info(f"🔍 Resolving ambiguous query with clarification: {clarification}")

            # Process clarification
            resolution_result = await self.nlp_processor.resolve_ambiguity(
                original_query, clarification, session_id
            )

            if resolution_result["resolved"]:
                # Execute scraping with resolved config
                extraction_config = resolution_result["extraction_config"]
                scrape_result = await self.scrape(url, original_query, extraction_config, session_id)

                # Add resolution metadata
                scrape_result["resolution_metadata"] = {
                    "original_query": original_query,
                    "clarification": clarification,
                    "final_intent": resolution_result["final_intent"],
                    "entities": resolution_result["entities"],
                    "resolution_timestamp": datetime.now().isoformat()
                }

                return scrape_result
            else:
                # Still needs clarification
                return {
                    "success": True,
                    "requires_clarification": True,
                    "ambiguity_check": resolution_result.get("ambiguity_check", {}),
                    "message": resolution_result["message"],
                    "url": url,
                    "original_query": original_query,
                    "session_id": session_id
                }

        except Exception as e:
            self.logger.error(f"❌ Ambiguity resolution failed: {e}")
            raise ScrapingError(f"Ambiguity resolution failed: {e}")
    
    async def multimodal_scrape(
        self,
        url: str,
        content_types: List[str] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape with multi-modal content processing
        """
        if not self.multimodal_processor:
            raise ScrapingError("Multi-Modal Processing not enabled")
        
        try:
            self.logger.info(f"📄 Starting multi-modal scrape for: {url}")
            
            if not content_types:
                content_types = ["text", "images"]
            
            results = {}
            for content_type in content_types:
                result = await self.multimodal_processor.process_content(url, content_type)
                results[content_type] = result
            
            return {
                "url": url,
                "content_types": content_types,
                "results": results,
                "method": "multimodal_processing",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Multi-modal scraping failed: {e}")
            raise ScrapingError(f"Multi-modal scraping failed: {e}")
    
    async def _basic_scrape(self, url: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Basic scraping fallback method"""
        # This would implement basic crawl4ai scraping
        # For now, return a placeholder
        return {
            "url": url,
            "config": config,
            "result": {"message": "Basic scraping not yet implemented"},
            "method": "basic_scrape",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get scraper status and health information"""
        status = {
            "initialized": self.is_initialized,
            "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None,
            "active_sessions": len(self.active_sessions),
            "components": {}
        }
        
        # Check component status - PRIORITIZE crawl4ai and Jina AI
        if self.crawl4ai_client:
            try:
                crawl4ai_info = await self.crawl4ai_client.get_service_info()
                status["components"]["crawl4ai_docker"] = {
                    "status": "healthy",
                    "service_info": crawl4ai_info,
                    "priority": "primary_scraping_engine"
                }
            except Exception as e:
                status["components"]["crawl4ai_docker"] = {
                    "status": "error",
                    "error": str(e),
                    "priority": "primary_scraping_engine"
                }

        if self.jina_ai_client:
            try:
                jina_ai_info = await self.jina_ai_client.get_service_status()
                status["components"]["jina_ai"] = {
                    "status": "healthy",
                    "service_info": jina_ai_info,
                    "priority": "core_ai_processing_engine"
                }
            except Exception as e:
                status["components"]["jina_ai"] = {
                    "status": "error",
                    "error": str(e),
                    "priority": "core_ai_processing_engine"
                }

        # Check performance optimizer status
        if self.performance_optimizer:
            try:
                performance_metrics = await self.performance_optimizer.get_performance_metrics()
                status["components"]["performance_optimizer"] = {
                    "status": "active",
                    "metrics": {
                        "crawl4ai_avg_response_time": performance_metrics.crawl4ai_avg_response_time,
                        "jina_ai_avg_response_time": performance_metrics.jina_ai_avg_response_time,
                        "cache_hit_rate": performance_metrics.cache_hit_rate,
                        "error_rate": performance_metrics.error_rate,
                        "total_requests": performance_metrics.total_requests,
                        "successful_requests": performance_metrics.successful_requests
                    },
                    "priority": "performance_enhancement"
                }
            except Exception as e:
                status["components"]["performance_optimizer"] = {
                    "status": "error",
                    "error": str(e),
                    "priority": "performance_enhancement"
                }

        if self.llm_manager:
            status["components"]["llm_manager"] = await self.llm_manager.get_status()

        if self.proxy_manager:
            status["components"]["proxy_manager"] = self.proxy_manager.get_proxy_statistics()
        
        return status

    async def cleanup(self):
        """Clean up resources and close connections"""
        try:
            self.logger.info("🧹 Cleaning up SwissKnife AI Scraper resources...")

            # Close crawl4ai Docker client
            if self.crawl4ai_client:
                await self.crawl4ai_client.close()
                self.logger.info("✅ crawl4ai Docker client closed")

            # Close Jina AI client
            if self.jina_ai_client:
                await self.jina_ai_client.close()
                self.logger.info("✅ Jina AI client closed")

            # Close performance optimizer
            if self.performance_optimizer:
                await self.performance_optimizer.close()
                self.logger.info("✅ Performance optimizer closed")

            # Close proxy manager
            if self.proxy_manager:
                await self.proxy_manager.cleanup()
                self.logger.info("✅ Proxy manager cleaned up")

            # Clear active sessions
            self.active_sessions.clear()

            self.logger.info("✅ SwissKnife AI Scraper cleanup completed")

        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

    def _determine_extraction_type(self, extraction_config: Optional[Dict[str, Any]], query: Optional[str]) -> str:
        """Determine the type of extraction being performed"""
        if not extraction_config and not query:
            return "basic"

        if extraction_config:
            if extraction_config.get("css_selectors"):
                return "css"
            elif extraction_config.get("xpath_expressions"):
                return "xpath"
            elif extraction_config.get("pdf") or extraction_config.get("multimodal"):
                return "multimodal"

        if query:
            return "llm"

        return "text"
    
    async def cleanup(self):
        """Cleanup resources and connections"""
        self.logger.info("🧹 Cleaning up SwissKnife AI Scraper...")
        
        # Cleanup components
        if self.llm_manager:
            await self.llm_manager.cleanup()
        
        if self.proxy_manager:
            await self.proxy_manager.shutdown()
        
        # Clear active sessions
        self.active_sessions.clear()
        
        self.is_initialized = False
        self.logger.info("✅ Cleanup completed")
