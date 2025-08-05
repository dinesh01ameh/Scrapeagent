"""
Tests for complex NLP features: ambiguity resolution, complex conditions, and multi-step conversations
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from features.natural_language_interface import (
    NaturalLanguageProcessor, 
    IntentType, 
    EntityType, 
    Intent, 
    Entity
)


class TestComplexNLPFeatures:
    """Test suite for complex NLP features"""

    @pytest.fixture
    def mock_llm_manager(self):
        """Mock LLM manager for testing"""
        mock_manager = Mock()
        mock_manager.process_content = AsyncMock(return_value='{"intent_type": "EXTRACT_DATA", "confidence": 0.9, "target_data": ["products"], "filters": {}, "conditions": []}')
        return mock_manager

    @pytest.fixture
    def nlp_processor(self, mock_llm_manager):
        """Create NLP processor instance for testing"""
        return NaturalLanguageProcessor(mock_llm_manager)

    @pytest.mark.asyncio
    async def test_parse_complex_conditions_if_then(self, nlp_processor):
        """Test parsing if-then conditional logic"""
        query = "if price is missing, then check the description for price information"
        intent = Intent(IntentType.EXTRACT_DATA, 0.8, ["products"], {}, [])
        
        conditions = await nlp_processor.parse_complex_conditions(query, intent)
        
        assert conditions["has_complex_logic"] == True
        assert len(conditions["conditional_rules"]) > 0
        
        rule = conditions["conditional_rules"][0]
        assert rule["type"] == "if_then"
        assert "price" in rule["condition"]
        assert "description" in rule["action"]

    @pytest.mark.asyncio
    async def test_parse_complex_conditions_multi_step(self, nlp_processor):
        """Test parsing multi-step logic"""
        query = "first extract all product titles, then get the prices for each product"
        intent = Intent(IntentType.EXTRACT_DATA, 0.8, ["products"], {}, [])
        
        conditions = await nlp_processor.parse_complex_conditions(query, intent)
        
        assert conditions["has_complex_logic"] == True
        assert len(conditions["multi_step_logic"]) >= 2
        
        step1 = conditions["multi_step_logic"][0]
        step2 = conditions["multi_step_logic"][1]
        
        assert step1["step_number"] == 1
        assert step2["step_number"] == 2
        assert step2["depends_on_previous"] == True

    @pytest.mark.asyncio
    async def test_parse_complex_conditions_fallback(self, nlp_processor):
        """Test parsing fallback strategies"""
        query = "get product prices, otherwise try to find them in the description"
        intent = Intent(IntentType.EXTRACT_DATA, 0.8, ["prices"], {}, [])
        
        conditions = await nlp_processor.parse_complex_conditions(query, intent)
        
        assert conditions["has_complex_logic"] == True
        assert len(conditions["fallback_strategies"]) > 0
        
        fallback = conditions["fallback_strategies"][0]
        assert fallback["type"] == "alternative"
        assert "description" in fallback["action"]

    @pytest.mark.asyncio
    async def test_parse_complex_conditions_error_handling(self, nlp_processor):
        """Test parsing error handling instructions"""
        query = "extract reviews, if that fails, get basic product info instead"
        intent = Intent(IntentType.EXTRACT_DATA, 0.8, ["reviews"], {}, [])
        
        conditions = await nlp_processor.parse_complex_conditions(query, intent)
        
        assert conditions["has_complex_logic"] == True
        assert len(conditions["error_handling"]) > 0
        
        error_rule = conditions["error_handling"][0]
        assert error_rule["trigger"] == "extraction_failure"
        assert "product info" in error_rule["action"]

    @pytest.mark.asyncio
    async def test_build_complex_extraction_config(self, nlp_processor):
        """Test building complex extraction configuration"""
        intent = Intent(IntentType.EXTRACT_DATA, 0.8, ["products"], {}, [])
        entities = []
        conditions = {
            "has_complex_logic": True,
            "conditional_rules": [{
                "condition": "price",
                "condition_value": "missing",
                "action": "check description",
                "type": "if_then",
                "confidence": 0.8
            }],
            "multi_step_logic": [{
                "step_number": 1,
                "action": "extract titles",
                "type": "sequential",
                "depends_on_previous": False
            }],
            "fallback_strategies": [{
                "action": "get basic info",
                "type": "alternative",
                "priority": "secondary"
            }],
            "complexity_score": 0.6
        }
        
        config = await nlp_processor.build_complex_extraction_config(intent, entities, conditions)
        
        assert config["execution_mode"] == "complex"
        assert "strategy_chain" in config
        assert "error_recovery" in config
        assert len(config["strategy_chain"]) > 0

    @pytest.mark.asyncio
    async def test_resolve_ambiguity_success(self, nlp_processor):
        """Test successful ambiguity resolution"""
        original_query = "get some data"
        clarification = "I want to extract product names and prices"
        session_id = "test_session"
        
        result = await nlp_processor.resolve_ambiguity(original_query, clarification, session_id)
        
        assert "resolved" in result
        if result["resolved"]:
            assert "extraction_config" in result
            assert "final_intent" in result

    @pytest.mark.asyncio
    async def test_start_multi_step_conversation(self, nlp_processor):
        """Test starting a multi-step conversation"""
        session_id = "test_session"
        initial_query = "first get all product titles, then extract prices for each product, finally analyze the price distribution"
        
        result = await nlp_processor.start_multi_step_conversation(session_id, initial_query)
        
        assert result["conversation_started"] == True
        if result["is_multi_step"]:
            assert result["total_steps"] > 1
            assert "current_step_details" in result

    @pytest.mark.asyncio
    async def test_continue_multi_step_conversation(self, nlp_processor):
        """Test continuing a multi-step conversation"""
        session_id = "test_session"
        
        # Setup conversation state
        nlp_processor.context_memory[session_id] = {
            "multi_step_state": {
                "active": True,
                "current_step": 1,
                "total_steps": 2,
                "completed_steps": [],
                "pending_steps": [
                    {
                        "step_id": "step_1",
                        "step_number": 1,
                        "description": "Extract product titles",
                        "type": "sequential",
                        "status": "pending"
                    },
                    {
                        "step_id": "step_2", 
                        "step_number": 2,
                        "description": "Extract prices",
                        "type": "sequential",
                        "status": "pending"
                    }
                ]
            }
        }
        
        user_response = "yes, that looks good"
        result = await nlp_processor.continue_multi_step_conversation(session_id, user_response)
        
        assert "step_completed" in result or "conversation_complete" in result

    def test_analyze_step_response_positive(self, nlp_processor):
        """Test analyzing positive user responses"""
        test_cases = [
            "yes",
            "ok",
            "sounds good",
            "proceed",
            "correct"
        ]
        
        current_step = {"description": "Extract products"}
        
        for response in test_cases:
            result = asyncio.run(nlp_processor._analyze_step_response(response, current_step))
            assert result["approved"] == True
            assert result["confidence"] > 0.5

    def test_analyze_step_response_negative(self, nlp_processor):
        """Test analyzing negative user responses"""
        test_cases = [
            ("no", False),
            ("not correct", False),
            ("change that", False),
            ("modify it", False),
            ("different approach", False),
            ("yes", True),  # Add a positive case to verify logic
        ]

        current_step = {"description": "Extract products"}

        for response, should_approve in test_cases:
            result = asyncio.run(nlp_processor._analyze_step_response(response, current_step))
            assert result["approved"] == should_approve
            if not should_approve:
                assert "modification_request" in result

    @pytest.mark.asyncio
    async def test_build_final_config_from_steps(self, nlp_processor):
        """Test building final configuration from conversation steps"""
        completed_steps = [
            {
                "step_id": "step_1",
                "step_number": 1,
                "description": "Extract product titles",
                "type": "sequential",
                "intent_type": "extract_data",
                "target_data": ["titles"],
                "estimated_time": 10
            },
            {
                "step_id": "step_2",
                "step_number": 2,
                "description": "Extract prices",
                "type": "sequential", 
                "intent_type": "extract_data",
                "target_data": ["prices"],
                "entities": [{"type": "price", "value": {"type": "max_price", "amount": 100}}],
                "estimated_time": 8
            }
        ]
        
        final_config = await nlp_processor._build_final_config_from_steps(completed_steps)
        
        assert final_config["execution_mode"] == "multi_step"
        assert len(final_config["step_sequence"]) == 2
        assert "titles" in final_config["target_data"]
        assert "prices" in final_config["target_data"]
        assert "price_filter" in final_config["filters"]

    def test_determine_strategy_for_action(self, nlp_processor):
        """Test strategy determination for different actions"""
        test_cases = [
            ("analyze sentiment", "llm"),
            ("extract email addresses", "regex"),
            ("get product titles", "css"),
            ("find phone numbers", "regex"),
            ("understand content", "llm"),
            ("get table data", "css")
        ]
        
        for action, expected_strategy in test_cases:
            strategy = nlp_processor._determine_strategy_for_action(action)
            assert strategy == expected_strategy

    def test_decompose_into_steps(self, nlp_processor):
        """Test query decomposition into steps"""
        query = "first get product titles, then extract prices, finally analyze price distribution"
        intent = Intent(IntentType.EXTRACT_DATA, 0.8, ["products"], {}, [])
        entities = []
        conditions = {
            "multi_step_logic": [
                {"step_number": 1, "action": "get product titles", "depends_on_previous": False},
                {"step_number": 2, "action": "extract prices", "depends_on_previous": True},
                {"step_number": 3, "action": "analyze price distribution", "depends_on_previous": True}
            ]
        }
        
        steps = nlp_processor._decompose_into_steps(query, intent, entities, conditions)
        
        assert len(steps) == 3
        assert steps[0]["step_number"] == 1
        assert steps[1]["depends_on"] == "step_1"
        assert steps[2]["depends_on"] == "step_2"

    def test_predict_next_intent(self, nlp_processor):
        """Test intent prediction based on conversation history"""
        session_id = "test_session"
        
        # Setup conversation history
        nlp_processor.context_memory[session_id] = {
            "conversation_history": [
                {
                    "intent": {"type": "extract_data", "target_data": ["products"]},
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "intent": {"type": "extract_data", "target_data": ["prices"]},
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "topic": "products"
        }
        
        predictions = nlp_processor.predict_next_intent(session_id)
        
        assert "predictions" in predictions
        if predictions["predictions"]:
            assert len(predictions["predictions"]) > 0
            assert "confidence" in predictions["predictions"][0]

    def test_analyze_conversation_patterns(self, nlp_processor):
        """Test conversation pattern analysis"""
        history = [
            {
                "intent": {
                    "type": "extract_data",
                    "confidence": 0.7,
                    "filters": {"price_filter": True},
                    "conditions": [],
                    "target_data": ["products"]
                }
            },
            {
                "intent": {
                    "type": "filter_content", 
                    "confidence": 0.8,
                    "filters": {"rating_filter": True},
                    "conditions": ["conditional"],
                    "target_data": ["reviews"]
                }
            }
        ]
        
        patterns = nlp_processor._analyze_conversation_patterns(history)
        
        assert "query_complexity_trend" in patterns
        assert "confidence_trend" in patterns
        assert "common_filters" in patterns
        assert "session_focus" in patterns
        assert len(patterns["confidence_trend"]) == 2


if __name__ == "__main__":
    pytest.main([__file__])
