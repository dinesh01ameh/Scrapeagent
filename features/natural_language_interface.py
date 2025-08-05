"""
Natural Language Interface for SwissKnife AI Scraper
Converts natural language commands to extraction strategies
"""

import asyncio
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from models.schemas import ExtractionConfig, ExtractionStrategy
from utils.exceptions import ScrapingError


class IntentType(str, Enum):
    """Types of scraping intents"""
    EXTRACT_DATA = "extract_data"
    FILTER_CONTENT = "filter_content"
    NAVIGATE_SITE = "navigate_site"
    ANALYZE_CONTENT = "analyze_content"
    COMPARE_DATA = "compare_data"
    MONITOR_CHANGES = "monitor_changes"


class EntityType(str, Enum):
    """Types of entities that can be extracted from queries"""
    PRICE = "price"
    RATING = "rating"
    DATE = "date"
    QUANTITY = "quantity"
    CATEGORY = "category"
    BRAND = "brand"
    LOCATION = "location"
    CONTACT = "contact"
    URL = "url"
    TEXT_CONTENT = "text_content"


@dataclass
class Intent:
    """Represents a parsed user intent"""
    type: IntentType
    confidence: float
    target_data: List[str]
    filters: Dict[str, Any]
    conditions: List[str]
    output_format: str = "json"


@dataclass
class Entity:
    """Represents an extracted entity from user query"""
    type: EntityType
    value: Any
    confidence: float
    context: str


class NaturalLanguageProcessor:
    """
    Convert natural language commands to extraction strategies
    """

    def __init__(self, local_llm_manager):
        self.llm_manager = local_llm_manager
        self.intent_patterns = self.load_intent_patterns()
        self.entity_patterns = self.load_entity_patterns()
        self.context_memory = {}
        self.logger = logging.getLogger(__name__)
    
    def load_intent_patterns(self) -> Dict[str, Any]:
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

    def load_entity_patterns(self) -> Dict[str, Any]:
        """Load regex patterns for entity extraction"""
        return {
            "price": {
                "patterns": [
                    r"\$(\d+(?:\.\d{2})?)",
                    r"(\d+(?:\.\d{2})?)\s*(?:dollars?|USD|€|euros?)",
                    r"under\s+\$?(\d+)",
                    r"over\s+\$?(\d+)",
                    r"between\s+\$?(\d+)\s*(?:and|-)?\s*\$?(\d+)"
                ],
                "examples": ["$50", "under $100", "between $20-$50"]
            },
            "rating": {
                "patterns": [
                    r"(\d+(?:\.\d+)?)\s*(?:stars?|rating)",
                    r"(\d+\+)\s*(?:stars?|rating)",  # Capture the + as well
                    r"above\s+(\d+(?:\.\d+)?)\s*(?:stars?|rating)",
                    r"(?:with|having)\s+(\d+\+?)\s*(?:stars?|rating)"
                ],
                "examples": ["4 stars", "5+ rating", "above 3.5 stars"]
            },
            "date": {
                "patterns": [
                    r"last\s+(\d+)\s+(days?|weeks?|months?)",
                    r"(?:in\s+)?(?:the\s+)?(?:past|last)\s+(week|month|year)",
                    r"(?:this|current)\s+(week|month|year)",
                    r"recent(?:ly)?",
                    r"today|yesterday"
                ],
                "examples": ["last 30 days", "this week", "recent", "yesterday"]
            },
            "quantity": {
                "patterns": [
                    r"(?:all|every)\s+(\w+)",
                    r"(?:first|top)\s+(\d+)\s+(\w+)",
                    r"(\d+)\s+(?:or\s+)?(?:more|less)\s+(\w+)"
                ],
                "examples": ["all products", "first 10 items", "5 or more reviews"]
            }
        }

    async def process_command(self, user_input: str, session_id: Optional[str] = None, check_ambiguity: bool = True, enable_complex_logic: bool = True) -> Dict[str, Any]:
        """
        Process natural language command and return extraction config with support for complex logic
        """
        try:
            self.logger.info(f"Processing command: {user_input}")

            # Parse intent and entities
            intent = await self.parse_intent(user_input)
            entities = await self.extract_entities(user_input)

            # Handle context from previous commands
            if session_id:
                context = self.context_memory.get(session_id, {})
                intent = self.apply_context(intent, context, user_input)

            # Check for ambiguity if requested
            if check_ambiguity:
                ambiguity_check = await self.detect_ambiguity(user_input, intent, entities)
                if ambiguity_check["is_ambiguous"]:
                    self.logger.info(f"Query is ambiguous (score: {ambiguity_check['ambiguity_score']:.2f})")
                    return {
                        "requires_clarification": True,
                        "ambiguity_check": ambiguity_check,
                        "partial_intent": {
                            "type": intent.type,
                            "confidence": intent.confidence,
                            "target_data": intent.target_data
                        },
                        "message": "I need some clarification to better understand your request."
                    }

            # Parse complex conditions if enabled
            conditions = {}
            if enable_complex_logic:
                conditions = await self.parse_complex_conditions(user_input, intent)

            # Update context memory
            if session_id:
                self.update_context_memory(session_id, user_input, intent, entities)

            # Choose extraction config builder based on complexity
            if conditions.get("has_complex_logic", False):
                self.logger.info("Using complex extraction config builder")
                extraction_config = await self.build_complex_extraction_config(intent, entities, conditions)
            else:
                self.logger.info("Using standard extraction config builder")
                extraction_config = await self.build_extraction_config(intent, entities)

            self.logger.info(f"Generated extraction config with mode: {extraction_config.get('execution_mode', 'standard')}")

            return {
                "requires_clarification": False,
                "extraction_config": extraction_config,
                "intent": {
                    "type": intent.type,
                    "confidence": intent.confidence,
                    "target_data": intent.target_data,
                    "filters": intent.filters,
                    "conditions": intent.conditions
                },
                "entities": [
                    {
                        "type": entity.type,
                        "value": entity.value,
                        "confidence": entity.confidence
                    } for entity in entities
                ],
                "complex_conditions": conditions if conditions.get("has_complex_logic", False) else None,
                "processing_metadata": {
                    "complexity_score": conditions.get("complexity_score", 0.0),
                    "execution_mode": extraction_config.get("execution_mode", "standard"),
                    "estimated_time": extraction_config.get("execution_metadata", {}).get("estimated_execution_time", 5),
                    "requires_llm": extraction_config.get("execution_metadata", {}).get("requires_llm", False)
                }
            }

        except Exception as e:
            self.logger.error(f"Error processing command '{user_input}': {e}")
            raise ScrapingError(f"Failed to process natural language command: {e}")
    
    async def parse_intent(self, user_input: str) -> Intent:
        """
        Use local LLM to understand user intent with fallback to pattern matching
        """
        try:
            # First try pattern-based classification for speed
            pattern_intent = self._classify_intent_by_patterns(user_input)

            if pattern_intent.confidence > 0.8:
                self.logger.info(f"High confidence pattern match: {pattern_intent.type}")
                return pattern_intent

            # Use LLM for complex queries
            llm_intent = await self._classify_intent_by_llm(user_input)

            # Combine pattern and LLM results for best accuracy
            final_intent = self._combine_intent_results(pattern_intent, llm_intent)

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

    def _classify_intent_by_patterns(self, user_input: str) -> Intent:
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

    async def _classify_intent_by_llm(self, user_input: str) -> Intent:
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

    def _combine_intent_results(self, pattern_intent: Intent, llm_intent: Intent) -> Intent:
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

    async def extract_entities(self, user_input: str) -> List[Entity]:
        """
        Extract entities (prices, ratings, dates, etc.) from user input
        """
        entities = []

        try:
            # Extract price entities
            price_entities = self._extract_price_entities(user_input)
            entities.extend(price_entities)

            # Extract rating entities
            rating_entities = self._extract_rating_entities(user_input)
            entities.extend(rating_entities)

            # Extract date entities
            date_entities = self._extract_date_entities(user_input)
            entities.extend(date_entities)

            # Extract quantity entities
            quantity_entities = self._extract_quantity_entities(user_input)
            entities.extend(quantity_entities)

            # Extract content type entities
            content_entities = self._extract_content_type_entities(user_input)
            entities.extend(content_entities)

            self.logger.info(f"Extracted {len(entities)} entities from query")
            return entities

        except Exception as e:
            self.logger.error(f"Error extracting entities: {e}")
            return []

    def _extract_price_entities(self, user_input: str) -> List[Entity]:
        """Extract price-related entities"""
        entities = []

        for pattern in self.entity_patterns["price"]["patterns"]:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 1:
                    # Single price value
                    value = float(match.group(1))
                    entity_type = "max_price" if "under" in match.group(0).lower() else "min_price" if "over" in match.group(0).lower() else "price"

                    entities.append(Entity(
                        type=EntityType.PRICE,
                        value={"type": entity_type, "amount": value},
                        confidence=0.9,
                        context=match.group(0)
                    ))
                elif len(match.groups()) == 2:
                    # Price range
                    min_price = float(match.group(1))
                    max_price = float(match.group(2))

                    entities.append(Entity(
                        type=EntityType.PRICE,
                        value={"type": "price_range", "min": min_price, "max": max_price},
                        confidence=0.95,
                        context=match.group(0)
                    ))

        return entities

    def _extract_rating_entities(self, user_input: str) -> List[Entity]:
        """Extract rating-related entities"""
        entities = []

        for pattern in self.entity_patterns["rating"]["patterns"]:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                rating_value = match.group(1)

                # Handle "4+" format
                if "+" in rating_value:
                    rating_num = float(rating_value.replace("+", ""))
                    entity_value = {"type": "min_rating", "value": rating_num}
                else:
                    rating_num = float(rating_value)
                    if "above" in match.group(0).lower():
                        entity_value = {"type": "min_rating", "value": rating_num}
                    else:
                        entity_value = {"type": "exact_rating", "value": rating_num}

                entities.append(Entity(
                    type=EntityType.RATING,
                    value=entity_value,
                    confidence=0.9,
                    context=match.group(0)
                ))

        return entities

    def _extract_date_entities(self, user_input: str) -> List[Entity]:
        """Extract date-related entities"""
        entities = []

        for pattern in self.entity_patterns["date"]["patterns"]:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                date_context = match.group(0).lower()

                if "last" in date_context or "past" in date_context:
                    if len(match.groups()) >= 2:
                        # "last 30 days" format
                        number = int(match.group(1))
                        unit = match.group(2).rstrip('s')  # Remove plural 's'

                        if unit == "day":
                            days_back = number
                        elif unit == "week":
                            days_back = number * 7
                        elif unit == "month":
                            days_back = number * 30
                        else:
                            days_back = 7  # Default fallback

                        cutoff_date = datetime.now() - timedelta(days=days_back)

                        entities.append(Entity(
                            type=EntityType.DATE,
                            value={"type": "after_date", "date": cutoff_date.isoformat()},
                            confidence=0.9,
                            context=match.group(0)
                        ))
                    else:
                        # "last week", "past month" format
                        unit = match.group(1)
                        if unit == "week":
                            days_back = 7
                        elif unit == "month":
                            days_back = 30
                        elif unit == "year":
                            days_back = 365
                        else:
                            days_back = 7

                        cutoff_date = datetime.now() - timedelta(days=days_back)

                        entities.append(Entity(
                            type=EntityType.DATE,
                            value={"type": "after_date", "date": cutoff_date.isoformat()},
                            confidence=0.8,
                            context=match.group(0)
                        ))

                elif "recent" in date_context:
                    # Recent = last 7 days
                    cutoff_date = datetime.now() - timedelta(days=7)
                    entities.append(Entity(
                        type=EntityType.DATE,
                        value={"type": "after_date", "date": cutoff_date.isoformat()},
                        confidence=0.7,
                        context=match.group(0)
                    ))

                elif "today" in date_context:
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    entities.append(Entity(
                        type=EntityType.DATE,
                        value={"type": "after_date", "date": today.isoformat()},
                        confidence=0.95,
                        context=match.group(0)
                    ))

        return entities

    def _extract_quantity_entities(self, user_input: str) -> List[Entity]:
        """Extract quantity-related entities"""
        entities = []

        for pattern in self.entity_patterns["quantity"]["patterns"]:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 1:
                    # "all products" format
                    entity_value = {"type": "all", "target": match.group(1)}
                elif len(match.groups()) == 2:
                    # "first 10 items" or "5 or more reviews" format
                    if "first" in match.group(0).lower() or "top" in match.group(0).lower():
                        entity_value = {"type": "limit", "count": int(match.group(1)), "target": match.group(2)}
                    else:
                        entity_value = {"type": "minimum", "count": int(match.group(1)), "target": match.group(2)}

                entities.append(Entity(
                    type=EntityType.QUANTITY,
                    value=entity_value,
                    confidence=0.8,
                    context=match.group(0)
                ))

        return entities

    def _extract_content_type_entities(self, user_input: str) -> List[Entity]:
        """Extract content type entities (products, reviews, articles, etc.)"""
        entities = []
        user_lower = user_input.lower()

        # Common content types and their patterns
        content_types = {
            "products": ["product", "item", "goods", "merchandise"],
            "reviews": ["review", "rating", "feedback", "comment"],
            "articles": ["article", "post", "blog", "news"],
            "jobs": ["job", "position", "vacancy", "opening"],
            "events": ["event", "meeting", "conference", "webinar"],
            "contacts": ["contact", "email", "phone", "address"],
            "prices": ["price", "cost", "fee", "rate"],
            "images": ["image", "photo", "picture", "img"],
            "links": ["link", "url", "href", "reference"]
        }

        for content_type, keywords in content_types.items():
            for keyword in keywords:
                if keyword in user_lower:
                    entities.append(Entity(
                        type=EntityType.TEXT_CONTENT,
                        value={"type": "content_type", "category": content_type},
                        confidence=0.7,
                        context=keyword
                    ))
                    break  # Only add one entity per content type

        return entities

    def _extract_price_entities(self, user_input: str) -> List[Entity]:
        """Extract price-related entities"""
        entities = []

        for pattern in self.entity_patterns["price"]["patterns"]:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 1:
                    # Single price value
                    value = float(match.group(1))
                    entity_type = "max_price" if "under" in match.group(0).lower() else "min_price" if "over" in match.group(0).lower() else "price"

                    entities.append(Entity(
                        type=EntityType.PRICE,
                        value={"type": entity_type, "amount": value},
                        confidence=0.9,
                        context=match.group(0)
                    ))
                elif len(match.groups()) == 2:
                    # Price range
                    min_price = float(match.group(1))
                    max_price = float(match.group(2))

                    entities.append(Entity(
                        type=EntityType.PRICE,
                        value={"type": "price_range", "min": min_price, "max": max_price},
                        confidence=0.95,
                        context=match.group(0)
                    ))

        return entities

    async def extract_entities(self, user_input: str) -> List[Entity]:
        """
        Extract entities (prices, ratings, dates, etc.) from user input
        """
        entities = []

        try:
            # Extract price entities
            price_entities = self._extract_price_entities(user_input)
            entities.extend(price_entities)

            # Extract rating entities
            rating_entities = self._extract_rating_entities(user_input)
            entities.extend(rating_entities)

            # Extract date entities
            date_entities = self._extract_date_entities(user_input)
            entities.extend(date_entities)

            # Extract quantity entities
            quantity_entities = self._extract_quantity_entities(user_input)
            entities.extend(quantity_entities)

            # Extract content type entities
            content_entities = self._extract_content_type_entities(user_input)
            entities.extend(content_entities)

            self.logger.info(f"Extracted {len(entities)} entities from query")
            return entities

        except Exception as e:
            self.logger.error(f"Error extracting entities: {e}")
            return []

    def apply_context(self, intent: Intent, context: Dict[str, Any], user_input: str) -> Intent:
        """
        Apply conversation context to refine intent understanding with advanced analysis
        """
        try:
            # Get conversation data
            previous_intents = context.get("previous_intents", [])
            previous_entities = context.get("previous_entities", [])
            conversation_topic = context.get("topic", None)
            conversation_history = context.get("conversation_history", [])

            # Analyze conversation patterns for better context application
            if conversation_history:
                patterns = self._analyze_conversation_patterns(conversation_history)
                session_focus = patterns.get("session_focus", "mixed")
                confidence_trend = patterns.get("confidence_trend", [])

                # Adjust confidence based on conversation patterns
                if session_focus == "focused" and len(confidence_trend) > 2:
                    avg_confidence = sum(confidence_trend[-3:]) / 3
                    if avg_confidence > 0.7:
                        intent.confidence = min(intent.confidence + 0.15, 0.95)
                        self.logger.info("Applied context: boosted confidence due to focused conversation")

            # Enhanced intent inference for low confidence queries
            if intent.confidence < 0.6 and previous_intents:
                last_intent = previous_intents[-1]

                # Progressive conversation patterns
                if any(word in user_input.lower() for word in ["also", "and", "too", "additionally", "plus"]):
                    intent.type = last_intent["type"]
                    intent.confidence = min(intent.confidence + 0.3, 0.9)
                    self.logger.info(f"Applied context: inherited intent type {intent.type} for additive query")

                # Refinement patterns
                elif any(word in user_input.lower() for word in ["but", "however", "instead", "rather"]):
                    # Keep same intent type but expect different filters
                    intent.type = last_intent["type"]
                    intent.confidence = min(intent.confidence + 0.25, 0.85)
                    self.logger.info(f"Applied context: inherited intent type {intent.type} for refinement query")

                # Continuation patterns
                elif any(phrase in user_input.lower() for phrase in ["then", "next", "after that", "now"]):
                    # Predict next logical step
                    if last_intent["type"] == "extract_data":
                        intent.type = IntentType.FILTER_CONTENT
                    elif last_intent["type"] == "filter_content":
                        intent.type = IntentType.ANALYZE_CONTENT
                    intent.confidence = min(intent.confidence + 0.2, 0.8)
                    self.logger.info(f"Applied context: predicted next step {intent.type}")

            # Smart target data merging based on conversation flow
            if conversation_topic and conversation_topic in user_input.lower():
                # Get most relevant previous targets
                recent_targets = []
                for prev_intent in previous_intents[-3:]:
                    if prev_intent.get("target_data"):
                        recent_targets.extend(prev_intent["target_data"])

                # Add targets that appear frequently in recent conversation
                if recent_targets:
                    target_frequency = {}
                    for target in recent_targets:
                        target_frequency[target] = target_frequency.get(target, 0) + 1

                    # Add frequently mentioned targets
                    for target, freq in target_frequency.items():
                        if freq >= 2 and target not in intent.target_data:
                            intent.target_data.append(target)

                    if target_frequency:
                        self.logger.info(f"Applied context: merged frequent targets from conversation")

            # Enhanced filter inheritance with smart merging
            reference_words = ["same", "similar", "like before", "as before", "previous", "last time"]
            if any(word in user_input.lower() for word in reference_words):
                # Find most recent intent with filters
                for prev_intent in reversed(previous_intents[-3:]):
                    if prev_intent.get("filters"):
                        # Smart filter merging - don't override explicit new filters
                        for filter_key, filter_value in prev_intent["filters"].items():
                            if filter_key not in intent.filters:
                                intent.filters[filter_key] = filter_value

                        intent.confidence = min(intent.confidence + 0.2, 0.9)
                        self.logger.info(f"Applied context: inherited {len(prev_intent['filters'])} filters")
                        break

            # Context-aware entity enhancement
            if previous_entities and len(previous_entities) > 0:
                # Look for entity patterns that might be relevant
                recent_price_entities = [e for e in previous_entities[-10:] if e.get("type") == "price"]
                recent_rating_entities = [e for e in previous_entities[-10:] if e.get("type") == "rating"]

                # If current query lacks specific criteria but previous queries had them
                if not intent.filters and (recent_price_entities or recent_rating_entities):
                    # Check if user is asking for "more" or "other" items
                    if any(word in user_input.lower() for word in ["more", "other", "different", "another"]):
                        # Suggest they might want similar criteria
                        intent.conditions.append("consider_previous_criteria")
                        self.logger.info("Applied context: flagged to consider previous criteria")

            # Temporal context awareness
            if conversation_history:
                last_interaction = conversation_history[-1]
                time_since_last = datetime.now() - datetime.fromisoformat(last_interaction["timestamp"])

                # If it's been a while, reduce context influence
                if time_since_last.total_seconds() > 3600:  # 1 hour
                    intent.confidence = max(intent.confidence - 0.1, 0.1)
                    self.logger.info("Applied context: reduced confidence due to time gap")
                # If very recent, boost confidence
                elif time_since_last.total_seconds() < 60:  # 1 minute
                    intent.confidence = min(intent.confidence + 0.1, 0.95)
                    self.logger.info("Applied context: boosted confidence due to immediate follow-up")

            return intent

        except Exception as e:
            self.logger.error(f"Error applying context: {e}")
            return intent

    def update_context_memory(self, session_id: str, user_input: str, intent: Intent, entities: List[Entity]) -> None:
        """
        Update conversation context memory for session
        """
        try:
            if session_id not in self.context_memory:
                self.context_memory[session_id] = {
                    "previous_intents": [],
                    "previous_entities": [],
                    "conversation_history": [],
                    "topic": None,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }

            context = self.context_memory[session_id]

            # Add current interaction to history
            context["conversation_history"].append({
                "user_input": user_input,
                "intent": {
                    "type": intent.type,
                    "confidence": intent.confidence,
                    "target_data": intent.target_data,
                    "filters": intent.filters,
                    "conditions": intent.conditions
                },
                "entities": [
                    {
                        "type": entity.type,
                        "value": entity.value,
                        "confidence": entity.confidence,
                        "context": entity.context
                    } for entity in entities
                ],
                "timestamp": datetime.now().isoformat()
            })

            # Keep only last 10 interactions to prevent memory bloat
            if len(context["conversation_history"]) > 10:
                context["conversation_history"] = context["conversation_history"][-10:]

            # Update previous intents (keep last 5)
            context["previous_intents"].append({
                "type": intent.type,
                "confidence": intent.confidence,
                "target_data": intent.target_data,
                "filters": intent.filters,
                "conditions": intent.conditions,
                "timestamp": datetime.now().isoformat()
            })
            if len(context["previous_intents"]) > 5:
                context["previous_intents"] = context["previous_intents"][-5:]

            # Update previous entities (keep last 20)
            for entity in entities:
                context["previous_entities"].append({
                    "type": entity.type,
                    "value": entity.value,
                    "confidence": entity.confidence,
                    "context": entity.context,
                    "timestamp": datetime.now().isoformat()
                })
            if len(context["previous_entities"]) > 20:
                context["previous_entities"] = context["previous_entities"][-20:]

            # Detect conversation topic from target data
            if intent.target_data:
                most_common_target = max(set(intent.target_data), key=intent.target_data.count)
                context["topic"] = most_common_target

            # Update timestamp
            context["last_updated"] = datetime.now().isoformat()

            self.logger.info(f"Updated context memory for session {session_id}")

        except Exception as e:
            self.logger.error(f"Error updating context memory: {e}")

    async def build_extraction_config(self, intent: Intent, entities: List[Entity]) -> Dict[str, Any]:
        """
        Convert Intent and Entity objects into ExtractionConfig for the scraper
        """
        try:
            # Start with base extraction configuration
            extraction_config = {
                "strategies": [],
                "fallback_enabled": True,
                "confidence_threshold": 0.7,
                "max_retries": 3,
                "filters": {},
                "output_format": intent.output_format,
                "metadata": {
                    "intent_type": intent.type,
                    "intent_confidence": intent.confidence,
                    "target_data": intent.target_data,
                    "processing_timestamp": datetime.now().isoformat()
                }
            }

            # Determine extraction strategies based on intent and entities
            strategies = []

            # Add CSS strategy for structured data
            if intent.type in [IntentType.EXTRACT_DATA, IntentType.FILTER_CONTENT]:
                strategies.append("css")

            # Add regex strategy for specific patterns (emails, phones, prices)
            if any(entity.type in [EntityType.CONTACT, EntityType.PRICE] for entity in entities):
                strategies.append("regex")

            # Add LLM strategy for complex analysis
            if intent.type in [IntentType.ANALYZE_CONTENT, IntentType.COMPARE_DATA]:
                strategies.append("llm")

            # Default to CSS + LLM if no specific strategy determined
            if not strategies:
                strategies = ["css", "llm"]

            extraction_config["strategies"] = strategies

            # Build filters from entities
            filters = {}

            for entity in entities:
                if entity.type == EntityType.PRICE:
                    if entity.value["type"] == "max_price":
                        filters["max_price"] = entity.value["amount"]
                    elif entity.value["type"] == "min_price":
                        filters["min_price"] = entity.value["amount"]
                    elif entity.value["type"] == "price_range":
                        filters["min_price"] = entity.value["min"]
                        filters["max_price"] = entity.value["max"]

                elif entity.type == EntityType.RATING:
                    if entity.value["type"] == "min_rating":
                        filters["min_rating"] = entity.value["value"]
                    elif entity.value["type"] == "exact_rating":
                        filters["exact_rating"] = entity.value["value"]

                elif entity.type == EntityType.DATE:
                    if entity.value["type"] == "after_date":
                        filters["after_date"] = entity.value["date"]

                elif entity.type == EntityType.QUANTITY:
                    if entity.value["type"] == "limit":
                        filters["limit"] = entity.value["count"]
                    elif entity.value["type"] == "minimum":
                        filters["minimum_count"] = entity.value["count"]

                elif entity.type == EntityType.TEXT_CONTENT:
                    if entity.value["type"] == "content_type":
                        filters["content_category"] = entity.value["category"]

            extraction_config["filters"] = filters

            # Add target selectors based on intent target data
            selectors = {}
            for target in intent.target_data:
                if target.lower() in ["product", "products"]:
                    selectors["products"] = [
                        ".product", ".item", "[data-product]", ".product-item",
                        ".product-card", ".listing-item"
                    ]
                elif target.lower() in ["price", "prices"]:
                    selectors["prices"] = [
                        ".price", ".cost", ".amount", "[data-price]",
                        ".price-current", ".sale-price", ".regular-price"
                    ]
                elif target.lower() in ["review", "reviews"]:
                    selectors["reviews"] = [
                        ".review", ".rating", ".feedback", "[data-review]",
                        ".review-item", ".customer-review"
                    ]
                elif target.lower() in ["title", "titles", "name", "names"]:
                    selectors["titles"] = [
                        "h1", "h2", "h3", ".title", ".name", "[data-title]",
                        ".product-title", ".item-name"
                    ]

            if selectors:
                extraction_config["selectors"] = selectors

            # Add LLM prompt if using LLM strategy
            if "llm" in strategies:
                llm_prompt = self._build_llm_prompt(intent, entities)
                extraction_config["llm_config"] = {
                    "prompt": llm_prompt,
                    "temperature": 0.1,
                    "max_tokens": 2000
                }

            self.logger.info(f"Built extraction config with {len(strategies)} strategies and {len(filters)} filters")
            return extraction_config

        except Exception as e:
            self.logger.error(f"Error building extraction config: {e}")
            # Return minimal fallback config
            return {
                "strategies": ["css"],
                "fallback_enabled": True,
                "confidence_threshold": 0.5,
                "max_retries": 2,
                "filters": {},
                "output_format": "json",
                "metadata": {
                    "error": str(e),
                    "fallback_config": True
                }
            }

    def _build_llm_prompt(self, intent: Intent, entities: List[Entity]) -> str:
        """
        Build LLM prompt based on intent and entities
        """
        prompt_parts = []

        # Base instruction
        if intent.type == IntentType.EXTRACT_DATA:
            prompt_parts.append("Extract the following data from the webpage content:")
        elif intent.type == IntentType.ANALYZE_CONTENT:
            prompt_parts.append("Analyze the webpage content and provide insights about:")
        elif intent.type == IntentType.FILTER_CONTENT:
            prompt_parts.append("Filter and extract content that matches these criteria:")
        else:
            prompt_parts.append("Process the webpage content to:")

        # Add target data
        if intent.target_data:
            prompt_parts.append(f"- Target data: {', '.join(intent.target_data)}")

        # Add entity-based criteria
        for entity in entities:
            if entity.type == EntityType.PRICE:
                if entity.value["type"] == "max_price":
                    prompt_parts.append(f"- Only include items under ${entity.value['amount']}")
                elif entity.value["type"] == "min_price":
                    prompt_parts.append(f"- Only include items over ${entity.value['amount']}")
                elif entity.value["type"] == "price_range":
                    prompt_parts.append(f"- Only include items between ${entity.value['min']} and ${entity.value['max']}")

            elif entity.type == EntityType.RATING:
                if entity.value["type"] == "min_rating":
                    prompt_parts.append(f"- Only include items with rating {entity.value['value']} or higher")

            elif entity.type == EntityType.DATE:
                if entity.value["type"] == "after_date":
                    prompt_parts.append(f"- Only include items from {entity.value['date']} onwards")

        # Add output format instruction
        prompt_parts.append(f"\nReturn the results in {intent.output_format.upper()} format.")
        prompt_parts.append("Be precise and only include data that clearly matches the criteria.")

        return "\n".join(prompt_parts)

    async def detect_ambiguity(self, user_input: str, intent: Intent, entities: List[Entity]) -> Dict[str, Any]:
        """
        Detect ambiguous queries and generate clarifying questions
        """
        try:
            ambiguity_score = 0.0
            ambiguity_reasons = []
            clarifying_questions = []

            # Check for low confidence intent
            if intent.confidence < 0.6:
                ambiguity_score += 0.3
                ambiguity_reasons.append("unclear_intent")
                clarifying_questions.append("What specific action would you like me to perform? (extract, analyze, filter, etc.)")

            # Check for missing target data
            if not intent.target_data or intent.target_data == ["content"]:
                ambiguity_score += 0.2
                ambiguity_reasons.append("missing_target_data")
                clarifying_questions.append("What specific information are you looking for? (products, prices, reviews, etc.)")

            # Check for conflicting entities
            price_entities = [e for e in entities if e.type == EntityType.PRICE]
            if len(price_entities) > 1:
                # Check for conflicting price ranges
                has_min = any("min_price" in str(e.value) for e in price_entities)
                has_max = any("max_price" in str(e.value) for e in price_entities)
                if has_min and has_max:
                    ambiguity_score += 0.1
                    ambiguity_reasons.append("conflicting_price_filters")
                    clarifying_questions.append("I found multiple price criteria. Could you clarify the exact price range you want?")

            # Check for vague terms
            vague_terms = ["stuff", "things", "items", "data", "information", "content"]
            user_lower = user_input.lower()
            if any(term in user_lower for term in vague_terms) and not intent.target_data:
                ambiguity_score += 0.2
                ambiguity_reasons.append("vague_terminology")
                clarifying_questions.append("Could you be more specific about what type of data you want to extract?")

            # Check for missing context (pronouns without clear reference)
            pronouns = ["it", "this", "that", "these", "those", "them"]
            if any(pronoun in user_lower.split() for pronoun in pronouns):
                ambiguity_score += 0.15
                ambiguity_reasons.append("unclear_reference")
                clarifying_questions.append("What does 'it/this/that' refer to in your request?")

            # Check for multiple possible interpretations
            if len(intent.target_data) > 3:
                ambiguity_score += 0.1
                ambiguity_reasons.append("too_many_targets")
                clarifying_questions.append("You mentioned several data types. Which ones are most important to you?")

            # Determine if query is ambiguous (threshold: 0.4)
            is_ambiguous = ambiguity_score >= 0.4

            result = {
                "is_ambiguous": is_ambiguous,
                "ambiguity_score": ambiguity_score,
                "reasons": ambiguity_reasons,
                "clarifying_questions": clarifying_questions,
                "confidence_threshold": 0.4,
                "suggestions": self._generate_query_suggestions(user_input, intent, entities) if is_ambiguous else []
            }

            if is_ambiguous:
                self.logger.info(f"Detected ambiguous query with score {ambiguity_score:.2f}")

            return result

        except Exception as e:
            self.logger.error(f"Error detecting ambiguity: {e}")
            return {
                "is_ambiguous": False,
                "ambiguity_score": 0.0,
                "reasons": [],
                "clarifying_questions": [],
                "suggestions": [],
                "error": str(e)
            }

    def _generate_query_suggestions(self, user_input: str, intent: Intent, entities: List[Entity]) -> List[str]:
        """
        Generate example queries to help users clarify their intent
        """
        suggestions = []

        # Base suggestions based on intent type
        if intent.type == IntentType.EXTRACT_DATA:
            suggestions.extend([
                "Get all products with prices under $100",
                "Extract all email addresses from the contact page",
                "Find all job listings with salary information"
            ])
        elif intent.type == IntentType.FILTER_CONTENT:
            suggestions.extend([
                "Show me products with 4+ star ratings",
                "Find articles published in the last 30 days",
                "Get reviews with ratings above 3.5 stars"
            ])
        elif intent.type == IntentType.ANALYZE_CONTENT:
            suggestions.extend([
                "Analyze the sentiment of customer reviews",
                "Categorize products by type",
                "Summarize the main topics in articles"
            ])

        # Add entity-specific suggestions
        if any(e.type == EntityType.PRICE for e in entities):
            suggestions.append("Get products between $50 and $200")

        if any(e.type == EntityType.RATING for e in entities):
            suggestions.append("Find items with exactly 5-star ratings")

        if any(e.type == EntityType.DATE for e in entities):
            suggestions.append("Extract posts from the last week")

        # Limit to 3 most relevant suggestions
        return suggestions[:3]

    async def resolve_ambiguity(self, user_input: str, clarification: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user's clarification to resolve ambiguity
        """
        try:
            self.logger.info(f"Resolving ambiguity with clarification: {clarification}")

            # Combine original input with clarification
            combined_input = f"{user_input} {clarification}"

            # Re-process with additional context
            intent = await self.parse_intent(combined_input)
            entities = await self.extract_entities(combined_input)

            # Apply session context if available
            if session_id and session_id in self.context_memory:
                context = self.context_memory[session_id]
                intent = self.apply_context(intent, context, combined_input)

            # Check if ambiguity is resolved
            ambiguity_check = await self.detect_ambiguity(combined_input, intent, entities)

            if not ambiguity_check["is_ambiguous"]:
                # Ambiguity resolved, build extraction config
                extraction_config = await self.build_extraction_config(intent, entities)

                # Update context memory
                if session_id:
                    self.update_context_memory(session_id, combined_input, intent, entities)

                return {
                    "resolved": True,
                    "extraction_config": extraction_config,
                    "final_intent": {
                        "type": intent.type,
                        "confidence": intent.confidence,
                        "target_data": intent.target_data,
                        "filters": intent.filters
                    },
                    "entities": [
                        {
                            "type": entity.type,
                            "value": entity.value,
                            "confidence": entity.confidence
                        } for entity in entities
                    ]
                }
            else:
                # Still ambiguous, return updated clarifying questions
                return {
                    "resolved": False,
                    "ambiguity_check": ambiguity_check,
                    "message": "I need a bit more clarification to understand your request better."
                }

        except Exception as e:
            self.logger.error(f"Error resolving ambiguity: {e}")
            return {
                "resolved": False,
                "error": str(e),
                "message": "I encountered an error while processing your clarification. Please try rephrasing your request."
            }

    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get a summary of the conversation for a session
        """
        try:
            if session_id not in self.context_memory:
                return {
                    "session_exists": False,
                    "message": "No conversation history found for this session"
                }

            context = self.context_memory[session_id]
            history = context.get("conversation_history", [])

            if not history:
                return {
                    "session_exists": True,
                    "conversation_count": 0,
                    "message": "No conversation history available"
                }

            # Analyze conversation patterns
            intent_types = [item["intent"]["type"] for item in history]
            most_common_intent = max(set(intent_types), key=intent_types.count) if intent_types else None

            target_data_all = []
            for item in history:
                target_data_all.extend(item["intent"]["target_data"])

            most_common_targets = []
            if target_data_all:
                target_counts = {}
                for target in target_data_all:
                    target_counts[target] = target_counts.get(target, 0) + 1
                most_common_targets = sorted(target_counts.items(), key=lambda x: x[1], reverse=True)[:3]

            # Get recent activity
            recent_queries = [item["user_input"] for item in history[-3:]]

            return {
                "session_exists": True,
                "session_id": session_id,
                "conversation_count": len(history),
                "created_at": context.get("created_at"),
                "last_updated": context.get("last_updated"),
                "current_topic": context.get("topic"),
                "most_common_intent": most_common_intent,
                "most_common_targets": [{"target": target, "count": count} for target, count in most_common_targets],
                "recent_queries": recent_queries,
                "total_entities_extracted": len(context.get("previous_entities", [])),
                "conversation_patterns": self._analyze_conversation_patterns(history)
            }

        except Exception as e:
            self.logger.error(f"Error getting conversation summary: {e}")
            return {
                "session_exists": False,
                "error": str(e),
                "message": "Error retrieving conversation summary"
            }

    def _analyze_conversation_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze patterns in conversation history
        """
        try:
            patterns = {
                "query_complexity_trend": [],
                "confidence_trend": [],
                "common_filters": {},
                "session_focus": "mixed",
                "learning_indicators": []
            }

            # Analyze query complexity over time
            for item in history:
                intent = item["intent"]
                complexity_score = 0

                # Base complexity from intent type
                if intent["type"] in ["analyze_content", "compare_data"]:
                    complexity_score += 0.3
                elif intent["type"] in ["filter_content", "extract_data"]:
                    complexity_score += 0.2

                # Add complexity from filters and conditions
                complexity_score += len(intent.get("filters", {})) * 0.1
                complexity_score += len(intent.get("conditions", [])) * 0.1
                complexity_score += len(intent.get("target_data", [])) * 0.05

                patterns["query_complexity_trend"].append(min(complexity_score, 1.0))
                patterns["confidence_trend"].append(intent["confidence"])

            # Analyze common filters
            all_filters = {}
            for item in history:
                filters = item["intent"].get("filters", {})
                for filter_key, filter_value in filters.items():
                    if filter_key not in all_filters:
                        all_filters[filter_key] = []
                    all_filters[filter_key].append(filter_value)

            patterns["common_filters"] = {
                key: {"count": len(values), "unique_values": len(set(str(v) for v in values))}
                for key, values in all_filters.items()
            }

            # Determine session focus
            intent_types = [item["intent"]["type"] for item in history]
            if len(set(intent_types)) == 1:
                patterns["session_focus"] = "focused"
            elif len(history) > 3 and len(set(intent_types[-3:])) == 1:
                patterns["session_focus"] = "converging"
            else:
                patterns["session_focus"] = "exploratory"

            # Detect learning indicators
            if len(patterns["confidence_trend"]) > 2:
                recent_confidence = sum(patterns["confidence_trend"][-3:]) / 3
                early_confidence = sum(patterns["confidence_trend"][:3]) / min(3, len(patterns["confidence_trend"]))

                if recent_confidence > early_confidence + 0.1:
                    patterns["learning_indicators"].append("improving_clarity")

                if patterns["query_complexity_trend"][-1] > patterns["query_complexity_trend"][0] + 0.2:
                    patterns["learning_indicators"].append("increasing_sophistication")

            return patterns

        except Exception as e:
            self.logger.error(f"Error analyzing conversation patterns: {e}")
            return {"error": str(e)}

    def predict_next_intent(self, session_id: str) -> Dict[str, Any]:
        """
        Predict what the user might want to do next based on conversation history
        """
        try:
            if session_id not in self.context_memory:
                return {"predictions": [], "confidence": 0.0}

            context = self.context_memory[session_id]
            history = context.get("conversation_history", [])

            if len(history) < 2:
                return {"predictions": [], "confidence": 0.0, "reason": "insufficient_history"}

            # Analyze recent patterns
            recent_intents = [item["intent"]["type"] for item in history[-3:]]
            recent_targets = []
            for item in history[-3:]:
                recent_targets.extend(item["intent"]["target_data"])

            predictions = []

            # Pattern 1: Continuation of current focus
            if len(set(recent_intents)) == 1:
                current_intent = recent_intents[0]
                if current_intent == "extract_data":
                    predictions.append({
                        "intent": "filter_content",
                        "confidence": 0.7,
                        "reason": "User has been extracting data, likely wants to filter next",
                        "suggested_query": f"Filter the {context.get('topic', 'data')} by specific criteria"
                    })
                elif current_intent == "filter_content":
                    predictions.append({
                        "intent": "analyze_content",
                        "confidence": 0.6,
                        "reason": "User has been filtering, might want analysis next",
                        "suggested_query": f"Analyze the filtered {context.get('topic', 'results')}"
                    })

            # Pattern 2: Expansion of scope
            if context.get("topic") and len(recent_targets) > 0:
                most_common_target = max(set(recent_targets), key=recent_targets.count)
                predictions.append({
                    "intent": "extract_data",
                    "confidence": 0.5,
                    "reason": "User might want to extract related data",
                    "suggested_query": f"Get additional information related to {most_common_target}"
                })

            # Pattern 3: Comparison or analysis
            if len(history) > 2 and any("extract" in intent for intent in recent_intents):
                predictions.append({
                    "intent": "compare_data",
                    "confidence": 0.4,
                    "reason": "User has extracted data, might want to compare",
                    "suggested_query": "Compare the extracted data across different criteria"
                })

            # Sort by confidence
            predictions.sort(key=lambda x: x["confidence"], reverse=True)

            return {
                "predictions": predictions[:3],  # Top 3 predictions
                "session_context": {
                    "current_topic": context.get("topic"),
                    "conversation_length": len(history),
                    "recent_focus": recent_intents[-1] if recent_intents else None
                }
            }

        except Exception as e:
            self.logger.error(f"Error predicting next intent: {e}")
            return {"predictions": [], "confidence": 0.0, "error": str(e)}

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up old conversation sessions to prevent memory bloat
        """
        try:
            current_time = datetime.now()
            sessions_cleaned = 0
            sessions_kept = 0

            sessions_to_remove = []

            for session_id, context in self.context_memory.items():
                last_updated_str = context.get("last_updated")
                if last_updated_str:
                    try:
                        last_updated = datetime.fromisoformat(last_updated_str)
                        age_hours = (current_time - last_updated).total_seconds() / 3600

                        if age_hours > max_age_hours:
                            sessions_to_remove.append(session_id)
                        else:
                            sessions_kept += 1
                    except ValueError:
                        # Invalid timestamp, remove session
                        sessions_to_remove.append(session_id)
                else:
                    # No timestamp, remove session
                    sessions_to_remove.append(session_id)

            # Remove old sessions
            for session_id in sessions_to_remove:
                del self.context_memory[session_id]
                sessions_cleaned += 1

            self.logger.info(f"Session cleanup: removed {sessions_cleaned}, kept {sessions_kept}")

            return {
                "sessions_cleaned": sessions_cleaned,
                "sessions_kept": sessions_kept,
                "cleanup_timestamp": current_time.isoformat(),
                "max_age_hours": max_age_hours
            }

        except Exception as e:
            self.logger.error(f"Error during session cleanup: {e}")
            return {"error": str(e), "sessions_cleaned": 0, "sessions_kept": 0}

    async def parse_complex_conditions(self, user_input: str, intent: Intent) -> Dict[str, Any]:
        """
        Parse complex conditional logic from user input
        """
        try:
            conditions = {
                "conditional_rules": [],
                "fallback_strategies": [],
                "multi_step_logic": [],
                "error_handling": [],
                "validation_rules": []
            }

            user_lower = user_input.lower()

            # Parse conditional statements (if/then/else logic)
            conditional_patterns = [
                r"if\s+(.+?)\s+(?:is|are)\s+(.+?),?\s+(?:then\s+)?(.+?)(?:\.|$|,\s*(?:otherwise|else))",
                r"when\s+(.+?),?\s+(?:then\s+)?(.+?)(?:\.|$|,\s*(?:otherwise|else))",
                r"unless\s+(.+?),?\s+(.+?)(?:\.|$)",
                r"in\s+case\s+(.+?),?\s+(.+?)(?:\.|$)"
            ]

            for pattern in conditional_patterns:
                matches = re.finditer(pattern, user_lower, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 3:
                        condition = match.group(1).strip()
                        condition_value = match.group(2).strip()
                        action = match.group(3).strip()

                        conditions["conditional_rules"].append({
                            "condition": condition,
                            "condition_value": condition_value,
                            "action": action,
                            "type": "if_then",
                            "confidence": 0.8
                        })
                    elif len(match.groups()) == 2:
                        condition = match.group(1).strip()
                        action = match.group(2).strip()

                        conditions["conditional_rules"].append({
                            "condition": condition,
                            "action": action,
                            "type": "unless" if "unless" in match.group(0) else "when",
                            "confidence": 0.7
                        })

            # Parse fallback strategies
            fallback_patterns = [
                r"(?:otherwise|else|if\s+not|failing\s+that),?\s+(.+?)(?:\.|$)",
                r"as\s+a\s+(?:backup|fallback|alternative),?\s+(.+?)(?:\.|$)",
                r"try\s+(.+?)\s+(?:first|initially),?\s+(?:then|and\s+then)\s+(.+?)(?:\.|$)"
            ]

            for pattern in fallback_patterns:
                matches = re.finditer(pattern, user_lower, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) == 1:
                        fallback_action = match.group(1).strip()
                        conditions["fallback_strategies"].append({
                            "action": fallback_action,
                            "type": "alternative",
                            "priority": "secondary",
                            "confidence": 0.7
                        })
                    elif len(match.groups()) == 2:
                        primary_action = match.group(1).strip()
                        secondary_action = match.group(2).strip()
                        conditions["fallback_strategies"].extend([
                            {
                                "action": primary_action,
                                "type": "primary",
                                "priority": "primary",
                                "confidence": 0.8
                            },
                            {
                                "action": secondary_action,
                                "type": "fallback",
                                "priority": "secondary",
                                "confidence": 0.7
                            }
                        ])

            # Parse multi-step logic
            step_patterns = [
                r"(?:first|initially|start\s+by)\s+(.+?),?\s+(?:then|next|after\s+that)\s+(.+?)(?:\.|$)",
                r"step\s+1:?\s*(.+?),?\s+step\s+2:?\s*(.+?)(?:\.|$)",
                r"(.+?),?\s+(?:and\s+)?then\s+(.+?),?\s+(?:and\s+)?(?:finally|lastly)\s+(.+?)(?:\.|$)"
            ]

            for pattern in step_patterns:
                matches = re.finditer(pattern, user_lower, re.IGNORECASE)
                for match in matches:
                    steps = [group.strip() for group in match.groups() if group]
                    for i, step in enumerate(steps):
                        conditions["multi_step_logic"].append({
                            "step_number": i + 1,
                            "action": step,
                            "type": "sequential",
                            "depends_on_previous": i > 0,
                            "confidence": 0.8
                        })

            # Parse error handling instructions
            error_patterns = [
                r"if\s+(?:that\s+)?(?:fails|doesn't\s+work|is\s+not\s+(?:found|available)),?\s+(.+?)(?:\.|$)",
                r"on\s+error,?\s+(.+?)(?:\.|$)",
                r"if\s+(?:no|zero)\s+results?,?\s+(.+?)(?:\.|$)"
            ]

            for pattern in error_patterns:
                matches = re.finditer(pattern, user_lower, re.IGNORECASE)
                for match in matches:
                    error_action = match.group(1).strip()
                    conditions["error_handling"].append({
                        "trigger": "extraction_failure",
                        "action": error_action,
                        "type": "error_recovery",
                        "confidence": 0.8
                    })

            # Parse validation rules
            validation_patterns = [
                r"(?:make\s+sure|ensure|verify\s+that)\s+(.+?)(?:\.|$)",
                r"(?:only\s+if|provided\s+that)\s+(.+?)(?:\.|$)",
                r"(?:must\s+(?:be|have)|should\s+(?:be|have))\s+(.+?)(?:\.|$)"
            ]

            for pattern in validation_patterns:
                matches = re.finditer(pattern, user_lower, re.IGNORECASE)
                for match in matches:
                    validation_rule = match.group(1).strip()
                    conditions["validation_rules"].append({
                        "rule": validation_rule,
                        "type": "pre_validation",
                        "required": True,
                        "confidence": 0.8
                    })

            # Calculate overall complexity score
            total_conditions = (
                len(conditions["conditional_rules"]) +
                len(conditions["fallback_strategies"]) +
                len(conditions["multi_step_logic"]) +
                len(conditions["error_handling"]) +
                len(conditions["validation_rules"])
            )

            conditions["complexity_score"] = min(total_conditions * 0.2, 1.0)
            conditions["has_complex_logic"] = total_conditions > 0

            self.logger.info(f"Parsed {total_conditions} complex conditions from query")
            return conditions

        except Exception as e:
            self.logger.error(f"Error parsing complex conditions: {e}")
            return {
                "conditional_rules": [],
                "fallback_strategies": [],
                "multi_step_logic": [],
                "error_handling": [],
                "validation_rules": [],
                "complexity_score": 0.0,
                "has_complex_logic": False,
                "error": str(e)
            }

    async def build_complex_extraction_config(self, intent: Intent, entities: List[Entity], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build extraction config with complex conditional logic and multi-step strategies
        """
        try:
            # Start with base config
            base_config = await self.build_extraction_config(intent, entities)

            # Enhance with complex logic
            complex_config = {
                **base_config,
                "execution_mode": "complex",
                "conditional_logic": conditions,
                "strategy_chain": [],
                "error_recovery": [],
                "validation_steps": [],
                "multi_step_execution": conditions.get("has_complex_logic", False)
            }

            # Build strategy chain based on conditions
            strategy_chain = []

            # Add primary strategies
            for rule in conditions.get("conditional_rules", []):
                strategy_step = {
                    "step_id": f"conditional_{len(strategy_chain) + 1}",
                    "type": "conditional",
                    "condition": {
                        "field": rule["condition"],
                        "operator": "exists" if "missing" not in rule.get("condition_value", "") else "not_exists",
                        "value": rule.get("condition_value", ""),
                        "confidence_threshold": 0.7
                    },
                    "action": {
                        "type": "extract",
                        "target": rule["action"],
                        "strategy": self._determine_strategy_for_action(rule["action"])
                    },
                    "on_success": "continue",
                    "on_failure": "try_fallback"
                }
                strategy_chain.append(strategy_step)

            # Add multi-step logic
            for step in conditions.get("multi_step_logic", []):
                strategy_step = {
                    "step_id": f"step_{step['step_number']}",
                    "type": "sequential",
                    "depends_on": f"step_{step['step_number'] - 1}" if step.get("depends_on_previous") else None,
                    "action": {
                        "type": "extract",
                        "target": step["action"],
                        "strategy": self._determine_strategy_for_action(step["action"])
                    },
                    "timeout": 30,
                    "retry_count": 2
                }
                strategy_chain.append(strategy_step)

            # Add fallback strategies
            for fallback in conditions.get("fallback_strategies", []):
                strategy_step = {
                    "step_id": f"fallback_{len(strategy_chain) + 1}",
                    "type": "fallback",
                    "priority": fallback.get("priority", "secondary"),
                    "trigger": "primary_failure",
                    "action": {
                        "type": "extract",
                        "target": fallback["action"],
                        "strategy": self._determine_strategy_for_action(fallback["action"])
                    }
                }
                strategy_chain.append(strategy_step)

            complex_config["strategy_chain"] = strategy_chain

            # Build error recovery steps
            error_recovery = []
            for error_rule in conditions.get("error_handling", []):
                recovery_step = {
                    "trigger": error_rule["trigger"],
                    "action": error_rule["action"],
                    "strategy": self._determine_strategy_for_action(error_rule["action"]),
                    "max_attempts": 3,
                    "backoff_strategy": "exponential"
                }
                error_recovery.append(recovery_step)

            complex_config["error_recovery"] = error_recovery

            # Build validation steps
            validation_steps = []
            for validation in conditions.get("validation_rules", []):
                validation_step = {
                    "rule": validation["rule"],
                    "type": validation["type"],
                    "required": validation.get("required", True),
                    "validation_strategy": "llm_verification",
                    "confidence_threshold": 0.8
                }
                validation_steps.append(validation_step)

            complex_config["validation_steps"] = validation_steps

            # Add execution metadata
            complex_config["execution_metadata"] = {
                "complexity_score": conditions.get("complexity_score", 0.0),
                "estimated_execution_time": len(strategy_chain) * 5,  # 5 seconds per step
                "requires_llm": any("llm" in str(step) for step in strategy_chain),
                "parallel_execution_possible": not any(step.get("depends_on") for step in strategy_chain),
                "created_at": datetime.now().isoformat()
            }

            self.logger.info(f"Built complex extraction config with {len(strategy_chain)} strategy steps")
            return complex_config

        except Exception as e:
            self.logger.error(f"Error building complex extraction config: {e}")
            # Return enhanced base config as fallback
            base_config["execution_mode"] = "simple"
            base_config["error"] = str(e)
            return base_config

    def _determine_strategy_for_action(self, action: str) -> str:
        """
        Determine the best extraction strategy for a given action
        """
        action_lower = action.lower()

        # LLM-based strategies for complex analysis
        if any(word in action_lower for word in ["analyze", "understand", "classify", "summarize", "interpret"]):
            return "llm"

        # Regex strategies for pattern-based extraction
        if any(word in action_lower for word in ["email", "phone", "url", "price", "date", "number"]):
            return "regex"

        # CSS strategies for structured content
        if any(word in action_lower for word in ["title", "heading", "link", "image", "table", "list"]):
            return "css"

        # Default to auto for unknown actions
        return "auto"

    async def start_multi_step_conversation(self, session_id: str, initial_query: str) -> Dict[str, Any]:
        """
        Start a multi-step conversation for building complex scraping tasks
        """
        try:
            self.logger.info(f"Starting multi-step conversation for session {session_id}")

            # Initialize or get existing conversation state
            if session_id not in self.context_memory:
                self.context_memory[session_id] = {
                    "previous_intents": [],
                    "previous_entities": [],
                    "conversation_history": [],
                    "topic": None,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "multi_step_state": {
                        "active": True,
                        "current_step": 1,
                        "total_steps": None,
                        "completed_steps": [],
                        "pending_steps": [],
                        "final_config": {},
                        "step_dependencies": {}
                    }
                }

            context = self.context_memory[session_id]
            multi_step_state = context["multi_step_state"]

            # Process initial query
            intent = await self.parse_intent(initial_query)
            entities = await self.extract_entities(initial_query)
            conditions = await self.parse_complex_conditions(initial_query, intent)

            # Determine if this is a multi-step query
            is_multi_step = (
                conditions.get("has_complex_logic", False) or
                len(conditions.get("multi_step_logic", [])) > 1 or
                any(word in initial_query.lower() for word in ["step", "then", "after", "next", "finally"])
            )

            if is_multi_step:
                # Break down into steps
                steps = self._decompose_into_steps(initial_query, intent, entities, conditions)
                multi_step_state["total_steps"] = len(steps)
                multi_step_state["pending_steps"] = steps

                # Start with first step
                current_step = steps[0] if steps else None

                return {
                    "conversation_started": True,
                    "is_multi_step": True,
                    "session_id": session_id,
                    "total_steps": len(steps),
                    "current_step": 1,
                    "current_step_details": current_step,
                    "next_action": "execute_step" if current_step else "clarify_requirements",
                    "message": f"I've broken down your request into {len(steps)} steps. Let's start with step 1: {current_step.get('description', '') if current_step else 'Please clarify your requirements.'}"
                }
            else:
                # Single step conversation
                multi_step_state["active"] = False
                extraction_config = await self.build_extraction_config(intent, entities)

                return {
                    "conversation_started": True,
                    "is_multi_step": False,
                    "session_id": session_id,
                    "extraction_config": extraction_config,
                    "message": "Your request can be handled in a single step. Ready to execute!"
                }

        except Exception as e:
            self.logger.error(f"Error starting multi-step conversation: {e}")
            return {
                "conversation_started": False,
                "error": str(e),
                "message": "Failed to start conversation. Please try rephrasing your request."
            }

    def _decompose_into_steps(self, query: str, intent: Intent, entities: List[Entity], conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decompose a complex query into manageable steps
        """
        try:
            steps = []
            step_counter = 1

            # Process explicit multi-step logic
            multi_step_logic = conditions.get("multi_step_logic", [])
            if multi_step_logic:
                for step_info in multi_step_logic:
                    step = {
                        "step_id": f"step_{step_counter}",
                        "step_number": step_counter,
                        "description": step_info["action"],
                        "type": "sequential",
                        "depends_on": f"step_{step_counter - 1}" if step_info.get("depends_on_previous") else None,
                        "intent_type": self._infer_intent_type_from_action(step_info["action"]),
                        "estimated_time": 10,
                        "status": "pending"
                    }
                    steps.append(step)
                    step_counter += 1

            # Process conditional rules as separate steps
            conditional_rules = conditions.get("conditional_rules", [])
            for rule in conditional_rules:
                step = {
                    "step_id": f"conditional_{step_counter}",
                    "step_number": step_counter,
                    "description": f"Check if {rule['condition']} {rule.get('condition_value', '')}, then {rule['action']}",
                    "type": "conditional",
                    "condition": rule,
                    "intent_type": self._infer_intent_type_from_action(rule["action"]),
                    "estimated_time": 8,
                    "status": "pending"
                }
                steps.append(step)
                step_counter += 1

            # If no explicit steps found, create logical steps based on intent and entities
            if not steps:
                # Primary extraction step
                primary_step = {
                    "step_id": f"primary_{step_counter}",
                    "step_number": step_counter,
                    "description": f"Extract {', '.join(intent.target_data)} from the webpage",
                    "type": "primary",
                    "intent_type": intent.type,
                    "target_data": intent.target_data,
                    "estimated_time": 15,
                    "status": "pending"
                }
                steps.append(primary_step)
                step_counter += 1

                # Add filtering step if entities suggest filtering
                if entities and any(e.type in [EntityType.PRICE, EntityType.RATING, EntityType.DATE] for e in entities):
                    filter_step = {
                        "step_id": f"filter_{step_counter}",
                        "step_number": step_counter,
                        "description": "Apply filters to the extracted data",
                        "type": "filter",
                        "depends_on": f"primary_{step_counter - 1}",
                        "intent_type": IntentType.FILTER_CONTENT,
                        "entities": [{"type": e.type, "value": e.value} for e in entities],
                        "estimated_time": 5,
                        "status": "pending"
                    }
                    steps.append(filter_step)
                    step_counter += 1

            # Add fallback steps
            fallback_strategies = conditions.get("fallback_strategies", [])
            for fallback in fallback_strategies:
                step = {
                    "step_id": f"fallback_{step_counter}",
                    "step_number": step_counter,
                    "description": f"Fallback: {fallback['action']}",
                    "type": "fallback",
                    "trigger": "primary_failure",
                    "intent_type": self._infer_intent_type_from_action(fallback["action"]),
                    "estimated_time": 12,
                    "status": "pending"
                }
                steps.append(step)
                step_counter += 1

            return steps

        except Exception as e:
            self.logger.error(f"Error decomposing query into steps: {e}")
            return []

    def _infer_intent_type_from_action(self, action: str) -> str:
        """
        Infer intent type from action description
        """
        action_lower = action.lower()

        if any(word in action_lower for word in ["extract", "get", "find", "collect", "scrape"]):
            return IntentType.EXTRACT_DATA
        elif any(word in action_lower for word in ["filter", "where", "with", "having", "under", "over"]):
            return IntentType.FILTER_CONTENT
        elif any(word in action_lower for word in ["analyze", "understand", "classify", "categorize"]):
            return IntentType.ANALYZE_CONTENT
        elif any(word in action_lower for word in ["compare", "versus", "against"]):
            return IntentType.COMPARE_DATA
        else:
            return IntentType.EXTRACT_DATA

    async def continue_multi_step_conversation(self, session_id: str, user_response: str) -> Dict[str, Any]:
        """
        Continue a multi-step conversation based on user response
        """
        try:
            if session_id not in self.context_memory:
                return {
                    "error": "Session not found",
                    "message": "Please start a new conversation."
                }

            context = self.context_memory[session_id]
            multi_step_state = context.get("multi_step_state", {})

            if not multi_step_state.get("active", False):
                return {
                    "error": "Multi-step conversation not active",
                    "message": "This session is not in multi-step mode."
                }

            current_step_num = multi_step_state.get("current_step", 1)
            pending_steps = multi_step_state.get("pending_steps", [])
            completed_steps = multi_step_state.get("completed_steps", [])

            # Find current step
            current_step = None
            for step in pending_steps:
                if step["step_number"] == current_step_num:
                    current_step = step
                    break

            if not current_step:
                return {
                    "conversation_complete": True,
                    "message": "All steps have been completed!",
                    "final_config": multi_step_state.get("final_config", {})
                }

            # Process user response for current step
            response_analysis = await self._analyze_step_response(user_response, current_step)

            if response_analysis["approved"]:
                # Mark step as completed
                current_step["status"] = "completed"
                current_step["user_approval"] = user_response
                current_step["completed_at"] = datetime.now().isoformat()
                completed_steps.append(current_step)

                # Remove from pending
                pending_steps = [s for s in pending_steps if s["step_number"] != current_step_num]
                multi_step_state["pending_steps"] = pending_steps
                multi_step_state["completed_steps"] = completed_steps

                # Move to next step
                next_step_num = current_step_num + 1
                multi_step_state["current_step"] = next_step_num

                # Find next step
                next_step = None
                for step in pending_steps:
                    if step["step_number"] == next_step_num:
                        next_step = step
                        break

                if next_step:
                    return {
                        "step_completed": True,
                        "current_step": next_step_num,
                        "total_steps": multi_step_state.get("total_steps", 0),
                        "next_step_details": next_step,
                        "message": f"Great! Step {current_step_num} completed. Now let's move to step {next_step_num}: {next_step.get('description', '')}"
                    }
                else:
                    # All steps completed
                    multi_step_state["active"] = False
                    final_config = await self._build_final_config_from_steps(completed_steps)
                    multi_step_state["final_config"] = final_config

                    return {
                        "conversation_complete": True,
                        "total_steps_completed": len(completed_steps),
                        "final_config": final_config,
                        "message": f"Excellent! All {len(completed_steps)} steps have been completed. Your scraping configuration is ready!"
                    }

            else:
                # User wants to modify the step
                modification_request = response_analysis.get("modification_request", "")

                return {
                    "step_modification_requested": True,
                    "current_step": current_step_num,
                    "modification_request": modification_request,
                    "current_step_details": current_step,
                    "message": f"I understand you'd like to modify step {current_step_num}. {modification_request}. Please provide more details or approve the step as is."
                }

        except Exception as e:
            self.logger.error(f"Error continuing multi-step conversation: {e}")
            return {
                "error": str(e),
                "message": "An error occurred while processing your response. Please try again."
            }

    async def _analyze_step_response(self, user_response: str, current_step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user response to determine if they approve the current step
        """
        try:
            response_lower = user_response.lower().strip()

            # Positive responses
            positive_indicators = [
                "yes", "ok", "okay", "good", "correct", "right", "approve", "proceed",
                "continue", "next", "sounds good", "looks good", "perfect", "exactly"
            ]

            # Negative responses
            negative_indicators = [
                "no", "not", "wrong", "incorrect", "change", "modify", "different",
                "instead", "rather", "but", "however", "actually"
            ]

            # Check for clear rejection/modification request FIRST (to catch "not correct" etc.)
            if any(indicator in response_lower for indicator in negative_indicators):
                return {
                    "approved": False,
                    "confidence": 0.8,
                    "modification_request": "User wants to modify this step",
                    "reason": "negative_response_detected"
                }

            # Check for clear approval
            if any(indicator in response_lower for indicator in positive_indicators):
                return {
                    "approved": True,
                    "confidence": 0.9,
                    "reason": "positive_response_detected"
                }

            # Check for specific modifications
            if any(word in response_lower for word in ["add", "remove", "include", "exclude", "also", "plus"]):
                return {
                    "approved": False,
                    "confidence": 0.7,
                    "modification_request": f"User wants to modify: {user_response}",
                    "reason": "modification_keywords_detected"
                }

            # Ambiguous response - ask for clarification
            return {
                "approved": False,
                "confidence": 0.3,
                "modification_request": "Response unclear - need clarification",
                "reason": "ambiguous_response"
            }

        except Exception as e:
            self.logger.error(f"Error analyzing step response: {e}")
            return {
                "approved": False,
                "confidence": 0.0,
                "modification_request": "Error processing response",
                "reason": "processing_error"
            }

    async def _build_final_config_from_steps(self, completed_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build final extraction configuration from completed conversation steps
        """
        try:
            final_config = {
                "execution_mode": "multi_step",
                "strategies": [],
                "step_sequence": [],
                "fallback_enabled": True,
                "confidence_threshold": 0.7,
                "max_retries": 3,
                "filters": {},
                "output_format": "json",
                "metadata": {
                    "conversation_based": True,
                    "total_steps": len(completed_steps),
                    "created_from_conversation": True,
                    "creation_timestamp": datetime.now().isoformat()
                }
            }

            all_target_data = []
            all_filters = {}
            strategies_used = set()

            # Process each completed step
            for step in completed_steps:
                step_config = {
                    "step_id": step["step_id"],
                    "step_number": step["step_number"],
                    "description": step["description"],
                    "type": step["type"],
                    "intent_type": step.get("intent_type", "extract_data"),
                    "status": "ready_for_execution"
                }

                # Add target data
                if step.get("target_data"):
                    all_target_data.extend(step["target_data"])
                    step_config["target_data"] = step["target_data"]

                # Add entities/filters
                if step.get("entities"):
                    for entity in step["entities"]:
                        if entity["type"] == "price":
                            all_filters.update({"price_filter": entity["value"]})
                        elif entity["type"] == "rating":
                            all_filters.update({"rating_filter": entity["value"]})
                        elif entity["type"] == "date":
                            all_filters.update({"date_filter": entity["value"]})

                # Determine strategy
                intent_type = step.get("intent_type", "extract_data")
                if intent_type == "analyze_content":
                    strategies_used.add("llm")
                elif intent_type == "extract_data":
                    strategies_used.add("css")
                elif intent_type == "filter_content":
                    strategies_used.add("regex")

                final_config["step_sequence"].append(step_config)

            # Set final configuration properties
            final_config["strategies"] = list(strategies_used) if strategies_used else ["css", "llm"]
            final_config["filters"] = all_filters
            final_config["target_data"] = list(set(all_target_data))

            # Add execution metadata
            final_config["execution_metadata"] = {
                "estimated_total_time": sum(step.get("estimated_time", 10) for step in completed_steps),
                "complexity_score": len(completed_steps) * 0.2,
                "requires_llm": "llm" in strategies_used,
                "parallel_execution_possible": not any(step.get("depends_on") for step in completed_steps)
            }

            return final_config

        except Exception as e:
            self.logger.error(f"Error building final config from steps: {e}")
            return {
                "execution_mode": "simple",
                "strategies": ["css"],
                "error": str(e),
                "fallback_config": True
            }