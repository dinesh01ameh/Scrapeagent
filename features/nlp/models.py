"""
Data models for Natural Language Processing
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List


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
