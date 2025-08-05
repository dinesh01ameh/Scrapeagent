"""
Intent Classification for Natural Language Processing
"""

import json
import re
import logging
from typing import Dict, Any, List

from .models import Intent, IntentType


class IntentClassifier:
    """Handles intent classification using patterns and LLM"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        self.logger = logging.getLogger(__name__)
        self.intent_patterns = self._load_intent_patterns()
    
    def _load_intent_patterns(self) -> Dict[str, Any]:
        """Load predefined intent patterns for quick classification"""
        return {
            "extract_data": {
                "keywords": ["get", "extract", "scrape", "find", "collect", "gather", "retrieve"],
                "patterns": [
                    r"get\s+(?:all\s+)?(\w+)",
                    r"extract\s+(?:all\s+)?(\w+)",
                    r"find\s+(?:all\s+)?(\w+)",
                    r"scrape\s+(?:all\s+)?(\w+)"
                ],
                "examples": ["get all products", "extract prices", "find reviews"]
            },
            "filter_content": {
                "keywords": ["under", "over", "above", "below", "between", "with", "having"],
                "patterns": [
                    r"under\s+\$?(\d+)",
                    r"over\s+\$?(\d+)",
                    r"above\s+(\d+(?:\.\d+)?)\s*(?:stars?|rating)",
                    r"with\s+(\d+\+?)\s*(?:stars?|rating)",
                    r"between\s+\$?(\d+)\s*(?:and|-)?\s*\$?(\d+)"
                ],
                "examples": ["under $50", "above 4 stars", "with 5+ rating"]
            },
            "analyze_content": {
                "keywords": ["analyze", "understand", "classify", "categorize", "summarize"],
                "patterns": [
                    r"analyze\s+(\w+)",
                    r"understand\s+(?:the\s+)?(\w+)",
                    r"classify\s+(?:the\s+)?(\w+)"
                ],
                "examples": ["analyze sentiment", "understand content", "classify products"]
            }
        }
    
    async def parse_intent(self, user_input: str) -> Intent:
        """Parse user intent using patterns and LLM fallback"""
        try:
            # First try pattern-based classification for speed
            pattern_intent = self._classify_by_patterns(user_input)
            
            if pattern_intent.confidence > 0.8:
                self.logger.info(f"High confidence pattern match: {pattern_intent.type}")
                return pattern_intent
            
            # Use LLM for complex queries
            llm_intent = await self._classify_by_llm(user_input)
            
            # Combine pattern and LLM results for best accuracy
            final_intent = self._combine_results(pattern_intent, llm_intent)
            
            return final_intent
            
        except Exception as e:
            self.logger.error(f"Error parsing intent: {e}")
            # Fallback to basic extraction intent
            return Intent(
                type=IntentType.EXTRACT_DATA,
                confidence=0.3,
                target_data=["content"],
                filters={},
                conditions=[]
            )
    
    def _classify_by_patterns(self, user_input: str) -> Intent:
        """Fast pattern-based intent classification"""
        user_lower = user_input.lower()
        
        # Check for extraction keywords
        extract_score = 0
        target_data = []
        filters = {}
        conditions = []
        
        for intent_type, patterns in self.intent_patterns.items():
            for keyword in patterns["keywords"]:
                if keyword in user_lower:
                    extract_score += 0.2
            
            for pattern in patterns["patterns"]:
                matches = re.findall(pattern, user_lower)
                if matches:
                    extract_score += 0.3
                    if intent_type == "extract_data":
                        target_data.extend([match if isinstance(match, str) else match[0] for match in matches])
        
        # Detect filtering criteria
        if any(word in user_lower for word in ["under", "over", "above", "below", "between"]):
            filters["has_price_filter"] = True
            extract_score += 0.2
        
        if any(word in user_lower for word in ["star", "rating", "review"]):
            filters["has_rating_filter"] = True
            extract_score += 0.2
        
        # Detect conditional logic
        if any(phrase in user_lower for phrase in ["if", "when", "unless", "in case"]):
            conditions.append("conditional_logic_detected")
            extract_score += 0.1
        
        confidence = min(extract_score, 1.0)
        
        return Intent(
            type=IntentType.EXTRACT_DATA,
            confidence=confidence,
            target_data=target_data or ["content"],
            filters=filters,
            conditions=conditions
        )
    
    async def _classify_by_llm(self, user_input: str) -> Intent:
        """Use LLM for sophisticated intent classification"""
        prompt = f"""
        Analyze this web scraping request and classify the intent:

        User Request: "{user_input}"

        Classify the intent as one of:
        1. EXTRACT_DATA - User wants to extract specific data from a website
        2. FILTER_CONTENT - User wants to filter extracted data by criteria
        3. ANALYZE_CONTENT - User wants to analyze or understand content
        4. COMPARE_DATA - User wants to compare data across sources
        5. MONITOR_CHANGES - User wants to track changes over time

        Also identify:
        - Target data types (products, prices, reviews, articles, etc.)
        - Filtering criteria (price ranges, ratings, dates, categories)
        - Any conditional logic or special requirements
        - Confidence level (0.0 to 1.0)

        Return a JSON response with this structure:
        {{
            "intent_type": "EXTRACT_DATA",
            "confidence": 0.9,
            "target_data": ["products", "prices"],
            "filters": {{"price_range": "under_50", "rating": "above_4"}},
            "conditions": ["if_price_missing_check_description"],
            "reasoning": "User wants to extract product data with price and rating filters"
        }}
        """
        
        try:
            response = await self.llm_manager.process_content(
                prompt,
                "intent_classification",
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse LLM response
            result = json.loads(response)
            
            return Intent(
                type=IntentType(result["intent_type"].lower()),
                confidence=result["confidence"],
                target_data=result["target_data"],
                filters=result["filters"],
                conditions=result["conditions"]
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse LLM intent response: {e}")
            # Return low-confidence fallback
            return Intent(
                type=IntentType.EXTRACT_DATA,
                confidence=0.4,
                target_data=["content"],
                filters={},
                conditions=[]
            )
    
    def _combine_results(self, pattern_intent: Intent, llm_intent: Intent) -> Intent:
        """Combine pattern and LLM results for optimal accuracy"""
        # Use the result with higher confidence as base
        if pattern_intent.confidence > llm_intent.confidence:
            base_intent = pattern_intent
            supplement_intent = llm_intent
        else:
            base_intent = llm_intent
            supplement_intent = pattern_intent
        
        # Merge target data and filters
        combined_target_data = list(set(base_intent.target_data + supplement_intent.target_data))
        combined_filters = {**base_intent.filters, **supplement_intent.filters}
        combined_conditions = list(set(base_intent.conditions + supplement_intent.conditions))
        
        # Average confidence with weight towards higher confidence result
        combined_confidence = (base_intent.confidence * 0.7 + supplement_intent.confidence * 0.3)
        
        return Intent(
            type=base_intent.type,
            confidence=combined_confidence,
            target_data=combined_target_data,
            filters=combined_filters,
            conditions=combined_conditions,
            output_format=base_intent.output_format
        )
