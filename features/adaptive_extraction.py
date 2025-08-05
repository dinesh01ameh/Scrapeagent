"""
Adaptive Extraction Engine - Core intelligence for strategy selection
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import hashlib
import json

from crawl4ai import AsyncWebCrawler
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

    def __init__(self, local_llm_config):
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
        """Fetch webpage content"""
        try:
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
        """Execute extraction with fallback chain"""

        # Try primary strategy first
        try:
            result = await primary_strategy.extract(content, user_query, url)
            if result and not result.get("error"):
                return result
        except Exception as e:
            self.logger.warning(f"Primary strategy {primary_strategy.name} failed: {e}")

        # Try fallback strategies
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