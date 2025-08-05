"""
SwissKnife AI Scraper - Core Scraper Implementation
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from config.settings import get_settings
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
        
        # Core components
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
            
            # Initialize Local LLM Manager
            if self.settings.ENABLE_NATURAL_LANGUAGE_INTERFACE or self.settings.ENABLE_CONTENT_INTELLIGENCE:
                self.logger.info("🤖 Initializing Local LLM Manager...")
                self.llm_manager = LocalLLMManager(self.settings.OLLAMA_ENDPOINT)
                await self.llm_manager.initialize()
                self.logger.info("✅ Local LLM Manager initialized")
            
            # Initialize Adaptive Extraction Engine
            if self.settings.ENABLE_ADAPTIVE_EXTRACTION:
                self.logger.info("🎯 Initializing Adaptive Extraction Engine...")
                self.extraction_engine = AdaptiveExtractionEngine(
                    local_llm_config={
                        "manager": self.llm_manager,
                        "default_model": self.settings.DEFAULT_MODEL
                    }
                )
                self.logger.info("✅ Adaptive Extraction Engine initialized")
            
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
            
            # Initialize Multi-Modal Processor
            if self.settings.ENABLE_MULTIMODAL_PROCESSING and self.llm_manager:
                self.logger.info("📄 Initializing Multi-Modal Processor...")
                jina_config = {
                    "api_key": self.settings.JINA_API_KEY,
                    "endpoint": self.settings.JINA_READER_ENDPOINT
                }
                self.multimodal_processor = MultiModalProcessor(self.llm_manager, jina_config)
                self.logger.info("✅ Multi-Modal Processor initialized")
            
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
            self.logger.info(f"🔍 Starting scrape for URL: {url}")
            
            # Use adaptive extraction if available
            if self.extraction_engine and query:
                result = await self.extraction_engine.analyze_and_extract(url, query)
                return {
                    "url": url,
                    "query": query,
                    "result": result,
                    "method": "adaptive_extraction",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Fallback to basic extraction
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
        
        # Check component status
        if self.llm_manager:
            status["components"]["llm_manager"] = await self.llm_manager.get_status()
        
        if self.proxy_manager:
            status["components"]["proxy_manager"] = self.proxy_manager.get_proxy_statistics()
        
        return status
    
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
