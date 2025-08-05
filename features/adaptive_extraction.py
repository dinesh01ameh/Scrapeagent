"""
Adaptive Extraction Engine - Core intelligence for strategy selection
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import hashlib
import json

from services.crawl4ai_client import Crawl4aiDockerClient
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

from models.schemas import ExtractionStrategy, ExtractionResult, ContentType
from utils.exceptions import ScrapingError


class BaseExtractionStrategy:
    """Base class for extraction strategies"""

    def __init__(self, name: str):
        self.name = name
        self.success_rate = 1.0
        self.avg_processing_time = 0.0

    async def extract(self, content: str, query: str, url: str) -> Dict[str, Any]:
        """Extract data using this strategy"""
        raise NotImplementedError

    def calculate_confidence(self, content: str, query: str) -> float:
        """Calculate confidence score for this strategy"""
        return 0.5  # Default confidence


class CSSExtractionStrategy(BaseExtractionStrategy):
    """CSS selector-based extraction"""

    def __init__(self):
        super().__init__("css")

    async def extract(self, content: str, query: str, url: str) -> Dict[str, Any]:
        """Extract using CSS selectors"""
        soup = BeautifulSoup(content, 'html.parser')

        # Try to infer CSS selectors from query
        selectors = self._infer_selectors(query)
        results = {}

        for field, selector in selectors.items():
            elements = soup.select(selector)
            if elements:
                results[field] = [elem.get_text(strip=True) for elem in elements]

        return results

    def _infer_selectors(self, query: str) -> Dict[str, str]:
        """Infer CSS selectors from natural language query"""
        # Simple mapping - in production, this would be more sophisticated
        selector_map = {
            'title': 'h1, h2, .title, [class*="title"]',
            'price': '.price, [class*="price"], [data-price]',
            'description': '.description, [class*="desc"]',
            'link': 'a[href]',
            'image': 'img[src]',
            'product': '.product, [class*="product"]',
            'review': '.review, [class*="review"]',
            'rating': '.rating, [class*="rating"], [class*="star"]'
        }

        inferred = {}
        query_lower = query.lower()

        for keyword, selector in selector_map.items():
            if keyword in query_lower:
                inferred[keyword] = selector

        return inferred if inferred else {'content': 'body'}

    def calculate_confidence(self, content: str, query: str) -> float:
        """Calculate confidence for CSS extraction"""
        soup = BeautifulSoup(content, 'html.parser')

        # Higher confidence if page has clear structure
        has_classes = len(soup.find_all(class_=True)) > 10
        has_ids = len(soup.find_all(id=True)) > 5

        confidence = 0.3
        if has_classes:
            confidence += 0.3
        if has_ids:
            confidence += 0.2

        return min(confidence, 1.0)


class XPathExtractionStrategy(BaseExtractionStrategy):
    """XPath-based extraction"""

    def __init__(self):
        super().__init__("xpath")

    async def extract(self, content: str, query: str, url: str) -> Dict[str, Any]:
        """Extract using XPath expressions"""
        # For now, return placeholder - full XPath implementation would require lxml
        return {"message": "XPath extraction not fully implemented yet"}

    def calculate_confidence(self, content: str, query: str) -> float:
        """Calculate confidence for XPath extraction"""
        # Lower confidence as fallback
        return 0.4


class RegexExtractionStrategy(BaseExtractionStrategy):
    """Regex-based extraction"""

    def __init__(self):
        super().__init__("regex")

    async def extract(self, content: str, query: str, url: str) -> Dict[str, Any]:
        """Extract using regex patterns"""
        patterns = self._get_patterns(query)
        results = {}

        for field, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                results[field] = matches

        return results

    def _get_patterns(self, query: str) -> Dict[str, str]:
        """Get regex patterns based on query"""
        pattern_map = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
            'price': r'\$\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*(?:USD|EUR|GBP)',
            'date': r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}'
        }

        relevant_patterns = {}
        query_lower = query.lower()

        for keyword, pattern in pattern_map.items():
            if keyword in query_lower:
                relevant_patterns[keyword] = pattern

        return relevant_patterns if relevant_patterns else {'text': r'.+'}

    def calculate_confidence(self, content: str, query: str) -> float:
        """Calculate confidence for regex extraction"""
        # Higher confidence for specific pattern queries
        specific_keywords = ['email', 'phone', 'url', 'price', 'date']
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in specific_keywords):
            return 0.8
        return 0.3


class LLMExtractionStrategy(BaseExtractionStrategy):
    """LLM-based extraction using local models"""

    def __init__(self, local_llm_config):
        super().__init__("llm")
        self.llm_manager = local_llm_config.get("manager")
        self.default_model = local_llm_config.get("default_model", "llama3.3")

    async def extract(self, content: str, query: str, url: str) -> Dict[str, Any]:
        """Extract using LLM analysis"""
        if not self.llm_manager:
            return {"error": "LLM manager not available"}

        # Truncate content if too long
        max_content_length = 4000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        prompt = f"""
        Analyze the following web content and extract information based on the user query.

        User Query: {query}

        Web Content:
        {content}

        Please extract the requested information and return it in JSON format.
        Focus on accuracy and relevance to the query.
        """

        try:
            result = await self.llm_manager.process_content(
                prompt,
                "extraction",
                self.default_model
            )

            # Try to parse as JSON, fallback to text
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"extracted_content": result}

        except Exception as e:
            return {"error": f"LLM extraction failed: {str(e)}"}

    def calculate_confidence(self, content: str, query: str) -> float:
        """Calculate confidence for LLM extraction"""
        # High confidence for complex queries
        complex_indicators = ['complex', 'analyze', 'understand', 'context', 'meaning']
        query_lower = query.lower()

        if any(indicator in query_lower for indicator in complex_indicators):
            return 0.9

        # Medium confidence for general queries
        return 0.7


class AdaptiveExtractionEngine:
    """
    Core intelligence that chooses the right extraction strategy
    """

    def __init__(self, local_llm_config, crawl4ai_client: Optional[Crawl4aiDockerClient] = None):
        # PRIORITY: Use crawl4ai Docker client for all extraction strategies
        self.crawl4ai_client = crawl4ai_client

        self.strategies = [
            CSSExtractionStrategy(),
            XPathExtractionStrategy(),
            RegexExtractionStrategy(),
            LLMExtractionStrategy(local_llm_config)
        ]
        self.pattern_cache = {}
        self.success_history = {}
        self.logger = logging.getLogger(__name__)

    async def analyze_and_extract(self, url: str, user_query: str) -> ExtractionResult:
        """
        Analyze content and automatically select best extraction approach
        """
        start_time = datetime.now()

        try:
            # 1. Fetch and analyze page content
            content = await self._fetch_content(url)
            page_analysis = await self.analyze_page_structure(content, url)

            # 2. Select optimal strategy based on content type and query
            strategy = self.select_strategy(page_analysis, user_query)

            # 3. Execute with fallback chain
            result = await self.execute_with_fallbacks(content, url, strategy, user_query)

            # 4. Learn from success/failure for future optimization
            processing_time = (datetime.now() - start_time).total_seconds()
            success = result.get("error") is None
            self.update_strategy_performance(url, strategy.name, success)

            return ExtractionResult(
                success=success,
                data=result,
                strategy_used=ExtractionStrategy(strategy.name),
                confidence=strategy.calculate_confidence(content, user_query),
                processing_time=processing_time,
                error=result.get("error")
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Extraction failed for {url}: {e}")

            return ExtractionResult(
                success=False,
                strategy_used=ExtractionStrategy.AUTO,
                processing_time=processing_time,
                error=str(e)
            )

    async def _fetch_content(self, url: str) -> str:
        """Fetch webpage content using crawl4ai Docker service (PRIORITY)"""
        try:
            # PRIORITY: Use crawl4ai Docker client if available
            if self.crawl4ai_client:
                self.logger.info(f"🚀 Fetching content via crawl4ai Docker service: {url}")
                result = await self.crawl4ai_client.crawl_url(url)
                return result.get("html", "") if result.get("success") else ""

            # FALLBACK: Direct crawl4ai (should not be reached in normal operation)
            self.logger.warning("⚠️ Using fallback crawl4ai method - Docker client not available")
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                return result.html if result.success else ""

        except Exception as e:
            raise ScrapingError(f"Failed to fetch content from {url}: {e}")

    async def analyze_page_structure(self, content: str, url: str) -> Dict[str, Any]:
        """Analyze page structure to inform strategy selection"""
        soup = BeautifulSoup(content, 'html.parser')

        analysis = {
            "url": url,
            "title": soup.title.string if soup.title else "",
            "has_structured_data": bool(soup.find_all(attrs={"itemtype": True})),
            "has_tables": len(soup.find_all("table")) > 0,
            "has_forms": len(soup.find_all("form")) > 0,
            "class_count": len(soup.find_all(class_=True)),
            "id_count": len(soup.find_all(id=True)),
            "content_length": len(content),
            "language": soup.get("lang", "unknown"),
            "meta_description": "",
        }

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            analysis["meta_description"] = meta_desc.get("content", "")

        return analysis

    def select_strategy(self, page_analysis: Dict[str, Any], user_query: str) -> BaseExtractionStrategy:
        """Select optimal extraction strategy"""
        strategy_scores = {}

        for strategy in self.strategies:
            # Base confidence from strategy
            confidence = strategy.calculate_confidence(
                page_analysis.get("content", ""),
                user_query
            )

            # Adjust based on historical performance
            url_domain = urlparse(page_analysis["url"]).netloc
            history_key = f"{url_domain}_{strategy.name}"

            if history_key in self.success_history:
                historical_success = self.success_history[history_key]["success_rate"]
                confidence = (confidence + historical_success) / 2

            strategy_scores[strategy] = confidence

        # Return strategy with highest confidence
        best_strategy = max(strategy_scores, key=strategy_scores.get)
        self.logger.info(f"Selected strategy: {best_strategy.name} (confidence: {strategy_scores[best_strategy]:.2f})")

        return best_strategy

    async def execute_with_fallbacks(
        self,
        content: str,
        url: str,
        primary_strategy: BaseExtractionStrategy,
        user_query: str
    ) -> Dict[str, Any]:
        """Execute extraction with fallback chain - PRIORITIZE crawl4ai Docker"""

        # PRIORITY 1: Try crawl4ai Docker service extraction methods
        if self.crawl4ai_client:
            crawl4ai_result = await self._try_crawl4ai_extraction(url, user_query, primary_strategy)
            if crawl4ai_result and not crawl4ai_result.get("error"):
                self.logger.info("✅ crawl4ai Docker extraction successful")
                return crawl4ai_result

        # FALLBACK 1: Try primary strategy with local processing
        try:
            self.logger.info(f"⚠️ Falling back to local strategy: {primary_strategy.name}")
            result = await primary_strategy.extract(content, user_query, url)
            if result and not result.get("error"):
                return result
        except Exception as e:
            self.logger.warning(f"Primary strategy {primary_strategy.name} failed: {e}")

        # FALLBACK 2: Try other strategies
        fallback_order = [s for s in self.strategies if s != primary_strategy]
        fallback_order.sort(key=lambda s: s.success_rate, reverse=True)

        for strategy in fallback_order:
            try:
                self.logger.info(f"Trying fallback strategy: {strategy.name}")
                result = await strategy.extract(content, user_query, url)
                if result and not result.get("error"):
                    return result
            except Exception as e:
                self.logger.warning(f"Fallback strategy {strategy.name} failed: {e}")
                continue

        return {"error": "All extraction strategies failed"}

    async def _try_crawl4ai_extraction(
        self,
        url: str,
        user_query: str,
        primary_strategy: BaseExtractionStrategy
    ) -> Optional[Dict[str, Any]]:
        """Try extraction using crawl4ai Docker service methods"""
        try:
            # Determine the best crawl4ai extraction method based on strategy
            if primary_strategy.name == "css":
                # Try to infer CSS selectors from query
                css_selectors = self._infer_css_selectors_from_query(user_query)
                if css_selectors:
                    self.logger.info(f"🎯 Using crawl4ai CSS extraction: {css_selectors}")
                    result = await self.crawl4ai_client.extract_with_css(url, css_selectors)
                    return self._format_crawl4ai_result(result)

            elif primary_strategy.name == "xpath":
                # Try to infer XPath expressions from query
                xpath_expressions = self._infer_xpath_from_query(user_query)
                if xpath_expressions:
                    self.logger.info(f"🎯 Using crawl4ai XPath extraction: {xpath_expressions}")
                    result = await self.crawl4ai_client.extract_with_xpath(url, xpath_expressions)
                    return self._format_crawl4ai_result(result)

            elif primary_strategy.name == "llm":
                # Use LLM extraction via crawl4ai
                self.logger.info(f"🤖 Using crawl4ai LLM extraction: {user_query}")
                result = await self.crawl4ai_client.extract_with_llm(url, user_query)
                return self._format_crawl4ai_result(result)

            # Default: Basic crawl with post-processing
            self.logger.info("🔍 Using crawl4ai basic crawl with intelligent post-processing")
            result = await self.crawl4ai_client.crawl_url(url)

            if result.get("success"):
                # Apply intelligent post-processing based on query
                processed_result = self._post_process_crawl4ai_result(result, user_query)
                return processed_result

            return None

        except Exception as e:
            self.logger.error(f"crawl4ai extraction failed: {e}")
            return None

    def update_strategy_performance(self, url: str, strategy_name: str, success: bool):
        """Update strategy performance metrics"""
        url_domain = urlparse(url).netloc
        history_key = f"{url_domain}_{strategy_name}"

        if history_key not in self.success_history:
            self.success_history[history_key] = {
                "total_attempts": 0,
                "successful_attempts": 0,
                "success_rate": 1.0
            }

        history = self.success_history[history_key]
        history["total_attempts"] += 1

        if success:
            history["successful_attempts"] += 1

        history["success_rate"] = history["successful_attempts"] / history["total_attempts"]

        # Update strategy's global success rate
        for strategy in self.strategies:
            if strategy.name == strategy_name:
                strategy.success_rate = history["success_rate"]
                break

    def _infer_css_selectors_from_query(self, query: str) -> Optional[Dict[str, str]]:
        """Infer CSS selectors from natural language query"""
        query_lower = query.lower()
        selectors = {}

        # Common patterns
        if "title" in query_lower:
            selectors["title"] = "h1, h2, title"
        if "price" in query_lower:
            selectors["price"] = ".price, .cost, [class*='price'], [class*='cost']"
        if "description" in query_lower:
            selectors["description"] = "p, .description, .summary"
        if "link" in query_lower:
            selectors["links"] = "a[href]"
        if "image" in query_lower:
            selectors["images"] = "img[src]"

        return selectors if selectors else None

    def _infer_xpath_from_query(self, query: str) -> Optional[Dict[str, str]]:
        """Infer XPath expressions from natural language query"""
        query_lower = query.lower()
        expressions = {}

        # Common XPath patterns
        if "title" in query_lower:
            expressions["title"] = "//h1/text() | //h2/text() | //title/text()"
        if "price" in query_lower:
            expressions["price"] = "//*[contains(@class, 'price')]/text()"
        if "description" in query_lower:
            expressions["description"] = "//p/text() | //*[contains(@class, 'description')]/text()"

        return expressions if expressions else None

    def _format_crawl4ai_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format crawl4ai result for consistency"""
        if not result.get("success"):
            return {"error": result.get("error_message", "crawl4ai extraction failed")}

        return {
            "extracted_data": result.get("extracted_content", {}),
            "html": result.get("html", ""),
            "markdown": result.get("markdown", ""),
            "metadata": result.get("metadata", {}),
            "source": "crawl4ai_docker",
            "success": True
        }

    def _post_process_crawl4ai_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Apply intelligent post-processing to crawl4ai results"""
        try:
            html_content = result.get("html", "")
            if not html_content:
                return {"error": "No HTML content to process"}

            # Use BeautifulSoup for intelligent extraction based on query
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_data = {}

            query_lower = query.lower()

            # Extract based on query intent
            if "title" in query_lower:
                title = soup.find('h1') or soup.find('title')
                if title:
                    extracted_data["title"] = title.get_text(strip=True)

            if "price" in query_lower:
                price_elements = soup.find_all(class_=lambda x: x and 'price' in x.lower())
                if price_elements:
                    extracted_data["prices"] = [elem.get_text(strip=True) for elem in price_elements]

            if "description" in query_lower:
                desc_elements = soup.find_all('p')[:3]  # First 3 paragraphs
                if desc_elements:
                    extracted_data["descriptions"] = [elem.get_text(strip=True) for elem in desc_elements]

            return {
                "extracted_data": extracted_data,
                "html": html_content,
                "markdown": result.get("markdown", ""),
                "metadata": result.get("metadata", {}),
                "source": "crawl4ai_docker_processed",
                "success": True
            }

        except Exception as e:
            self.logger.error(f"Post-processing failed: {e}")
            return {"error": f"Post-processing failed: {e}"}