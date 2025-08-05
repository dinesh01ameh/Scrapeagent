"""
Integration tests for Natural Language Interface with real scenarios
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from features.natural_language_interface import NaturalLanguageProcessor


class TestNLPIntegration:
    """Integration tests for NLP with scraper"""

    @pytest.fixture
    def mock_llm_manager(self):
        """Mock LLM manager for testing"""
        mock_manager = Mock()
        mock_manager.process_content = AsyncMock()
        mock_manager.initialize = AsyncMock()
        return mock_manager

    # Removed mock_scraper_components as we're not testing the full scraper

    @pytest.mark.asyncio
    async def test_end_to_end_simple_query(self, mock_llm_manager):
        """Test end-to-end processing of a simple query"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        
        # Mock LLM response for intent classification
        mock_llm_manager.process_content.return_value = '''
        {
            "intent_type": "EXTRACT_DATA",
            "confidence": 0.9,
            "target_data": ["products", "prices"],
            "filters": {"price_range": "under_100"},
            "conditions": [],
            "reasoning": "User wants to extract product data with price filter"
        }
        '''
        
        query = "Get all products under $100 with their prices"
        result = await nlp_processor.process_command(query, check_ambiguity=False)
        
        assert result["requires_clarification"] == False
        assert "extraction_config" in result
        assert "intent" in result
        assert "entities" in result
        
        # Check extraction config structure
        config = result["extraction_config"]
        assert "strategies" in config
        assert "filters" in config
        assert "max_price" in config["filters"]
        assert config["filters"]["max_price"] == 100.0

    @pytest.mark.asyncio
    async def test_end_to_end_complex_query(self, mock_llm_manager):
        """Test end-to-end processing of a complex query with conditions"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        
        query = "Get all products under $50, but if price is missing, check the description for price info"
        result = await nlp_processor.process_command(query, enable_complex_logic=True)
        
        assert "extraction_config" in result
        config = result["extraction_config"]
        
        # Should use complex execution mode
        if config.get("execution_mode") == "complex":
            assert "strategy_chain" in config
            assert "conditional_logic" in config
            assert len(config["strategy_chain"]) > 0

    @pytest.mark.asyncio
    async def test_ambiguity_detection_and_resolution(self, mock_llm_manager):
        """Test ambiguity detection and resolution workflow"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        
        # Step 1: Process ambiguous query
        ambiguous_query = "get some stuff from the page"
        result1 = await nlp_processor.process_command(ambiguous_query, check_ambiguity=True)
        
        # Should detect ambiguity
        if result1.get("requires_clarification"):
            assert "ambiguity_check" in result1
            assert result1["ambiguity_check"]["is_ambiguous"] == True
            
            # Step 2: Resolve with clarification
            clarification = "I want to extract product names and prices"
            result2 = await nlp_processor.resolve_ambiguity(
                ambiguous_query, clarification, "test_session"
            )
            
            if result2.get("resolved"):
                assert "extraction_config" in result2
                assert "final_intent" in result2

    @pytest.mark.asyncio
    async def test_multi_step_conversation_workflow(self, mock_llm_manager):
        """Test complete multi-step conversation workflow"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        session_id = "integration_test_session"
        
        # Step 1: Start conversation
        initial_query = "First get all product titles, then extract prices for each, finally calculate average price"
        start_result = await nlp_processor.start_multi_step_conversation(session_id, initial_query)
        
        assert start_result["conversation_started"] == True
        
        if start_result["is_multi_step"]:
            total_steps = start_result["total_steps"]
            assert total_steps > 1
            
            # Step 2: Continue through each step
            for step_num in range(1, total_steps + 1):
                user_response = "yes, proceed with this step"
                continue_result = await nlp_processor.continue_multi_step_conversation(
                    session_id, user_response
                )
                
                if continue_result.get("conversation_complete"):
                    assert "final_config" in continue_result
                    break
                elif continue_result.get("step_completed"):
                    assert continue_result["current_step"] == step_num + 1

    @pytest.mark.asyncio
    async def test_context_awareness_across_queries(self, mock_llm_manager):
        """Test context awareness across multiple queries in a session"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        session_id = "context_test_session"
        
        # Query 1: Establish context
        query1 = "Get all products under $100"
        result1 = await nlp_processor.process_command(query1, session_id=session_id)
        
        # Query 2: Follow-up that should use context
        query2 = "Also get the reviews for those items"
        result2 = await nlp_processor.process_command(query2, session_id=session_id)
        
        # Check that context was applied
        context = nlp_processor.context_memory.get(session_id, {})
        assert len(context.get("conversation_history", [])) == 2
        assert context.get("topic") is not None

    @pytest.mark.asyncio
    async def test_real_world_ecommerce_scenario(self, mock_llm_manager):
        """Test realistic e-commerce scraping scenario"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        
        test_scenarios = [
            {
                "query": "Find all laptops under $1000 with 4+ star ratings",
                "expected_entities": ["price", "rating", "content_type"],
                "expected_filters": ["max_price", "min_rating"]
            },
            {
                "query": "Get product reviews posted in the last 30 days with sentiment analysis",
                "expected_entities": ["date", "content_type"],
                "expected_intent": "analyze_content"
            },
            {
                "query": "Extract all contact information including emails and phone numbers",
                "expected_entities": ["content_type"],
                "expected_strategies": ["regex"]
            }
        ]
        
        for scenario in test_scenarios:
            result = await nlp_processor.process_command(
                scenario["query"], 
                check_ambiguity=False
            )
            
            assert "extraction_config" in result
            config = result["extraction_config"]
            
            # Check expected entities were extracted
            entities = result.get("entities", [])
            entity_types = [entity["type"] for entity in entities]
            
            for expected_entity in scenario.get("expected_entities", []):
                # At least one entity of expected type should be found
                assert any(expected_entity in entity_type for entity_type in entity_types)
            
            # Check expected filters
            for expected_filter in scenario.get("expected_filters", []):
                assert expected_filter in config.get("filters", {})
            
            # Check expected intent
            if "expected_intent" in scenario:
                assert result["intent"]["type"] == scenario["expected_intent"]
            
            # Check expected strategies
            if "expected_strategies" in scenario:
                for expected_strategy in scenario["expected_strategies"]:
                    assert expected_strategy in config.get("strategies", [])

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, mock_llm_manager):
        """Test error handling and recovery mechanisms"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        
        # Test with malformed LLM response
        mock_llm_manager.process_content.return_value = "invalid json response"
        
        query = "analyze customer sentiment"
        result = await nlp_processor.process_command(query, check_ambiguity=False)
        
        # Should still return a valid result with fallback
        assert "extraction_config" in result
        assert result["intent"]["confidence"] > 0  # Should have fallback confidence

    @pytest.mark.asyncio
    async def test_performance_with_complex_queries(self, mock_llm_manager):
        """Test performance with complex queries"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        
        complex_query = """
        First, extract all product titles and descriptions from the main catalog page.
        Then, for each product, get the price information - if the price is not visible,
        check the product detail page. After that, collect all customer reviews with
        ratings above 3 stars posted in the last 6 months. Finally, analyze the
        sentiment of these reviews and categorize them by product category.
        If any step fails, try alternative extraction methods and log the issues.
        """
        
        import time
        start_time = time.time()
        
        result = await nlp_processor.process_command(
            complex_query, 
            enable_complex_logic=True
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 5.0  # 5 seconds max
        
        assert "extraction_config" in result
        config = result["extraction_config"]
        
        if config.get("execution_mode") == "complex":
            assert "strategy_chain" in config
            assert len(config["strategy_chain"]) > 3  # Multiple steps detected

    def test_conversation_memory_management(self, mock_llm_manager):
        """Test conversation memory management and cleanup"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        
        # Create multiple sessions
        for i in range(10):
            session_id = f"session_{i}"
            nlp_processor.update_context_memory(
                session_id, 
                f"query {i}", 
                Mock(type="extract_data", confidence=0.8, target_data=["data"], filters={}, conditions=[]),
                []
            )
        
        assert len(nlp_processor.context_memory) == 10
        
        # Test cleanup
        cleanup_result = nlp_processor.cleanup_old_sessions(max_age_hours=0)  # Clean all
        
        assert cleanup_result["sessions_cleaned"] == 10
        assert len(nlp_processor.context_memory) == 0

    @pytest.mark.asyncio
    async def test_conversation_summary_and_predictions(self, mock_llm_manager):
        """Test conversation summary and prediction features"""
        nlp_processor = NaturalLanguageProcessor(mock_llm_manager)
        session_id = "summary_test_session"
        
        # Build conversation history
        queries = [
            "get all products",
            "filter by price under $50", 
            "get reviews for those products"
        ]
        
        for query in queries:
            await nlp_processor.process_command(query, session_id=session_id)
        
        # Test summary
        summary = nlp_processor.get_conversation_summary(session_id)
        assert summary["session_exists"] == True
        assert summary["conversation_count"] == 3
        assert len(summary["recent_queries"]) > 0
        
        # Test predictions
        predictions = nlp_processor.predict_next_intent(session_id)
        assert "predictions" in predictions
        if predictions["predictions"]:
            assert "confidence" in predictions["predictions"][0]
            assert "suggested_query" in predictions["predictions"][0]


if __name__ == "__main__":
    pytest.main([__file__])
