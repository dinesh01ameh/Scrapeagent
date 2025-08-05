"""
Entity Extraction for Natural Language Processing
"""

import re
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from .models import Entity, EntityType


class EntityExtractor:
    """Handles entity extraction from user input"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.entity_patterns = self._load_entity_patterns()
    
    def _load_entity_patterns(self) -> Dict[str, Any]:
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
                    r"(\d+\+)\s*(?:stars?|rating)",
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
    
    async def extract_entities(self, user_input: str) -> List[Entity]:
        """Extract entities (prices, ratings, dates, etc.) from user input"""
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
