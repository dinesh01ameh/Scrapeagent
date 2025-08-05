"""
Pytest configuration and shared fixtures for Natural Language Interface tests
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# Removed event_loop fixture to avoid conflicts with pytest-asyncio


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager for testing"""
    mock_manager = Mock()
    mock_manager.process_content = AsyncMock()
    mock_manager.initialize = AsyncMock()
    
    # Default response for intent classification
    mock_manager.process_content.return_value = '''
    {
        "intent_type": "EXTRACT_DATA",
        "confidence": 0.9,
        "target_data": ["products"],
        "filters": {},
        "conditions": [],
        "reasoning": "User wants to extract product data"
    }
    '''
    
    return mock_manager


@pytest.fixture
def sample_intent():
    """Sample intent for testing"""
    from features.natural_language_interface import Intent, IntentType
    
    return Intent(
        type=IntentType.EXTRACT_DATA,
        confidence=0.8,
        target_data=["products", "prices"],
        filters={"price_filter": True},
        conditions=["conditional_logic"],
        output_format="json"
    )


@pytest.fixture
def sample_entities():
    """Sample entities for testing"""
    from features.natural_language_interface import Entity, EntityType
    
    return [
        Entity(
            type=EntityType.PRICE,
            value={"type": "max_price", "amount": 100.0},
            confidence=0.9,
            context="under $100"
        ),
        Entity(
            type=EntityType.RATING,
            value={"type": "min_rating", "value": 4.0},
            confidence=0.8,
            context="4+ stars"
        ),
        Entity(
            type=EntityType.TEXT_CONTENT,
            value={"type": "content_type", "category": "products"},
            confidence=0.7,
            context="products"
        )
    ]


@pytest.fixture
def sample_conversation_context():
    """Sample conversation context for testing"""
    from datetime import datetime
    
    return {
        "previous_intents": [
            {
                "type": "extract_data",
                "confidence": 0.8,
                "target_data": ["products"],
                "filters": {"price_filter": True},
                "timestamp": datetime.now().isoformat()
            }
        ],
        "previous_entities": [
            {
                "type": "price",
                "value": {"type": "max_price", "amount": 50.0},
                "confidence": 0.9,
                "timestamp": datetime.now().isoformat()
            }
        ],
        "conversation_history": [
            {
                "user_input": "get products under $50",
                "intent": {
                    "type": "extract_data",
                    "confidence": 0.8,
                    "target_data": ["products"],
                    "filters": {"price_filter": True}
                },
                "entities": [
                    {
                        "type": "price",
                        "value": {"type": "max_price", "amount": 50.0},
                        "confidence": 0.9
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
        ],
        "topic": "products",
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }


@pytest.fixture
def sample_complex_conditions():
    """Sample complex conditions for testing"""
    return {
        "has_complex_logic": True,
        "conditional_rules": [
            {
                "condition": "price",
                "condition_value": "missing",
                "action": "check description",
                "type": "if_then",
                "confidence": 0.8
            }
        ],
        "fallback_strategies": [
            {
                "action": "get basic info",
                "type": "alternative",
                "priority": "secondary",
                "confidence": 0.7
            }
        ],
        "multi_step_logic": [
            {
                "step_number": 1,
                "action": "extract titles",
                "type": "sequential",
                "depends_on_previous": False,
                "confidence": 0.8
            },
            {
                "step_number": 2,
                "action": "extract prices",
                "type": "sequential", 
                "depends_on_previous": True,
                "confidence": 0.8
            }
        ],
        "error_handling": [
            {
                "trigger": "extraction_failure",
                "action": "try alternative method",
                "type": "error_recovery",
                "confidence": 0.8
            }
        ],
        "validation_rules": [
            {
                "rule": "ensure price is numeric",
                "type": "pre_validation",
                "required": True,
                "confidence": 0.8
            }
        ],
        "complexity_score": 0.6
    }


@pytest.fixture
def sample_multi_step_state():
    """Sample multi-step conversation state for testing"""
    return {
        "active": True,
        "current_step": 1,
        "total_steps": 3,
        "completed_steps": [],
        "pending_steps": [
            {
                "step_id": "step_1",
                "step_number": 1,
                "description": "Extract product titles",
                "type": "sequential",
                "intent_type": "extract_data",
                "estimated_time": 10,
                "status": "pending"
            },
            {
                "step_id": "step_2",
                "step_number": 2,
                "description": "Extract prices",
                "type": "sequential",
                "depends_on": "step_1",
                "intent_type": "extract_data",
                "estimated_time": 8,
                "status": "pending"
            },
            {
                "step_id": "step_3",
                "step_number": 3,
                "description": "Analyze price distribution",
                "type": "sequential",
                "depends_on": "step_2",
                "intent_type": "analyze_content",
                "estimated_time": 12,
                "status": "pending"
            }
        ],
        "final_config": {},
        "step_dependencies": {
            "step_2": ["step_1"],
            "step_3": ["step_2"]
        }
    }


# Test data for various scenarios
TEST_QUERIES = {
    "simple": [
        "get all products",
        "find reviews",
        "extract prices",
        "scrape contact information"
    ],
    "with_filters": [
        "get products under $50",
        "find reviews with 4+ stars",
        "extract articles from last week",
        "get jobs with salary information"
    ],
    "complex": [
        "get products under $50, but if price is missing, check description",
        "first extract titles, then get prices for each item",
        "find reviews with 4+ stars, unless there are fewer than 10 reviews",
        "extract emails and phones, if that fails, get contact page links"
    ],
    "ambiguous": [
        "get some stuff",
        "find things",
        "extract data",
        "scrape information"
    ],
    "multi_step": [
        "first get product titles, then extract prices, finally analyze distribution",
        "step 1: find all articles, step 2: extract authors, step 3: analyze topics",
        "start by getting contact info, then verify emails, lastly format results"
    ]
}


@pytest.fixture
def test_queries():
    """Test queries for various scenarios"""
    return TEST_QUERIES


# Performance test configuration
PERFORMANCE_THRESHOLDS = {
    "simple_query_processing": 1.0,  # seconds
    "complex_query_processing": 3.0,  # seconds
    "ambiguity_detection": 0.5,  # seconds
    "context_application": 0.2,  # seconds
    "entity_extraction": 0.5,  # seconds
}


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing"""
    return PERFORMANCE_THRESHOLDS


# Mock responses for different scenarios
MOCK_LLM_RESPONSES = {
    "extract_data": '''
    {
        "intent_type": "EXTRACT_DATA",
        "confidence": 0.9,
        "target_data": ["products", "prices"],
        "filters": {"price_range": "under_100"},
        "conditions": [],
        "reasoning": "User wants to extract product data with price filter"
    }
    ''',
    "analyze_content": '''
    {
        "intent_type": "ANALYZE_CONTENT",
        "confidence": 0.85,
        "target_data": ["reviews", "sentiment"],
        "filters": {},
        "conditions": ["sentiment_analysis"],
        "reasoning": "User wants to analyze content sentiment"
    }
    ''',
    "filter_content": '''
    {
        "intent_type": "FILTER_CONTENT",
        "confidence": 0.8,
        "target_data": ["products"],
        "filters": {"rating_filter": "above_4", "price_filter": "under_50"},
        "conditions": [],
        "reasoning": "User wants to filter content by criteria"
    }
    '''
}


@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses for different scenarios"""
    return MOCK_LLM_RESPONSES
