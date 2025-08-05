"""
Performance tests and benchmarks for Natural Language Interface
Tests processing speed, memory usage, and scalability
"""

import pytest
import asyncio
import time
import psutil
import os
from unittest.mock import Mock, AsyncMock
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from features.natural_language_interface import NaturalLanguageProcessor


class TestPerformance:
    """Performance and scalability tests"""

    @pytest.fixture
    def mock_llm_manager(self):
        """Mock LLM manager with fast responses"""
        mock_manager = Mock()
        mock_manager.process_content = AsyncMock()
        mock_manager.initialize = AsyncMock()
        
        # Fast mock response
        mock_manager.process_content.return_value = '''
        {
            "intent_type": "EXTRACT_DATA",
            "confidence": 0.9,
            "target_data": ["products"],
            "filters": {},
            "conditions": []
        }
        '''
        return mock_manager

    @pytest.fixture
    def nlp_processor(self, mock_llm_manager):
        """Create NLP processor instance for testing"""
        return NaturalLanguageProcessor(mock_llm_manager)

    def test_simple_query_performance(self, nlp_processor):
        """Test performance of simple queries"""
        queries = [
            "get all products",
            "find reviews",
            "extract prices",
            "scrape contact info",
            "get job listings"
        ]
        
        times = []
        
        for query in queries:
            start_time = time.time()
            
            result = asyncio.run(nlp_processor.process_command(
                query, 
                check_ambiguity=False
            ))
            
            end_time = time.time()
            processing_time = end_time - start_time
            times.append(processing_time)
            
            # Verify result is valid
            assert "extraction_config" in result
            assert processing_time < 0.5  # Should be very fast for simple queries
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"Simple queries - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
        assert avg_time < 0.2  # Average should be under 200ms
        assert max_time < 0.5  # No query should take more than 500ms

    def test_complex_query_performance(self, nlp_processor):
        """Test performance of complex queries"""
        complex_queries = [
            "Get all products under $100 with 4+ star ratings from verified sellers posted in last 30 days",
            "Find job listings for senior software engineers with salary over $120k at tech companies in San Francisco with remote options",
            "Extract all articles about artificial intelligence published this week by reputable sources with more than 1000 shares",
            "Get product reviews with detailed analysis, sentiment scores, and user demographics for items in electronics category",
            "Find real estate listings for 3+ bedroom houses under $500k with good school districts and low crime rates"
        ]
        
        times = []
        
        for query in complex_queries:
            start_time = time.time()
            
            result = asyncio.run(nlp_processor.process_command(
                query, 
                check_ambiguity=False,
                enable_complex_logic=True
            ))
            
            end_time = time.time()
            processing_time = end_time - start_time
            times.append(processing_time)
            
            # Verify result is valid
            assert "extraction_config" in result
            assert processing_time < 2.0  # Complex queries should still be under 2s
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"Complex queries - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
        assert avg_time < 1.0  # Average should be under 1 second
        assert max_time < 2.0  # No query should take more than 2 seconds

    @pytest.mark.asyncio
    async def test_entity_extraction_performance(self, nlp_processor):
        """Test performance of entity extraction with many entities"""
        # Query with many different entity types
        entity_heavy_query = """
        Find all products between $50 and $500 with 4+ star ratings,
        posted in the last 7 days, with more than 100 reviews,
        from verified sellers, with free shipping,
        in electronics category, with warranty included,
        available in blue or black colors, size medium or large,
        compatible with iPhone 12 or newer models
        """

        start_time = time.time()

        entities = await nlp_processor.extract_entities(entity_heavy_query)

        end_time = time.time()
        processing_time = end_time - start_time

        print(f"Entity extraction - {len(entities)} entities in {processing_time:.3f}s")

        # Should extract multiple entities quickly
        assert len(entities) >= 5  # Should find multiple entity types
        assert processing_time < 1.0  # Should be fast even with many entities

    def test_concurrent_processing(self, nlp_processor):
        """Test concurrent query processing"""
        queries = [
            "get products under $100",
            "find reviews with 4+ stars", 
            "extract job listings with salary",
            "get articles from last week",
            "find contact information"
        ] * 4  # 20 queries total
        
        async def process_query(query):
            return await nlp_processor.process_command(
                query, 
                check_ambiguity=False
            )
        
        async def run_concurrent_test():
            start_time = time.time()
            
            # Process all queries concurrently
            tasks = [process_query(query) for query in queries]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            return results, total_time
        
        results, total_time = asyncio.run(run_concurrent_test())
        
        # Verify all results are valid
        for result in results:
            assert "extraction_config" in result
        
        avg_time_per_query = total_time / len(queries)
        
        print(f"Concurrent processing - {len(queries)} queries in {total_time:.3f}s (avg: {avg_time_per_query:.3f}s per query)")
        
        # Concurrent processing should be efficient
        assert total_time < 5.0  # All 20 queries should complete in under 5 seconds
        assert avg_time_per_query < 0.5  # Average per query should be reasonable

    def test_memory_usage(self, nlp_processor):
        """Test memory usage during processing"""
        process = psutil.Process(os.getpid())
        
        # Get baseline memory usage
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process many queries to test memory usage
        queries = [
            f"get products under ${price}" for price in range(10, 1000, 10)
        ]  # 99 queries
        
        for query in queries:
            result = asyncio.run(nlp_processor.process_command(
                query, 
                check_ambiguity=False
            ))
            assert "extraction_config" in result
        
        # Check memory usage after processing
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory
        
        print(f"Memory usage - Baseline: {baseline_memory:.1f}MB, Final: {final_memory:.1f}MB, Increase: {memory_increase:.1f}MB")
        
        # Memory increase should be reasonable
        assert memory_increase < 50  # Should not increase by more than 50MB

    def test_context_memory_performance(self, nlp_processor):
        """Test performance with large conversation contexts"""
        session_id = "performance_test_session"
        
        # Create a large conversation history
        start_time = time.time()
        
        for i in range(100):  # 100 interactions
            query = f"get products in category {i % 10}"
            result = asyncio.run(nlp_processor.process_command(
                query, 
                session_id=session_id,
                check_ambiguity=False
            ))
            assert "extraction_config" in result
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100
        
        print(f"Context memory performance - 100 interactions in {total_time:.3f}s (avg: {avg_time:.3f}s)")
        
        # Performance should not degrade significantly with context
        assert avg_time < 0.1  # Average should still be fast
        
        # Check context memory size
        context = nlp_processor.context_memory.get(session_id, {})
        history_size = len(context.get("conversation_history", []))
        
        print(f"Context history size: {history_size} entries")
        
        # Should maintain reasonable history size (due to cleanup)
        assert history_size <= 10  # Should be limited by cleanup logic

    def test_ambiguity_detection_performance(self, nlp_processor):
        """Test performance of ambiguity detection"""
        ambiguous_queries = [
            "get some data",
            "find things",
            "extract information", 
            "scrape stuff",
            "get content"
        ] * 10  # 50 queries
        
        start_time = time.time()
        
        for query in ambiguous_queries:
            result = asyncio.run(nlp_processor.process_command(
                query, 
                check_ambiguity=True
            ))
            # Should either have extraction_config or require clarification
            assert "extraction_config" in result or result.get("requires_clarification")
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(ambiguous_queries)
        
        print(f"Ambiguity detection - {len(ambiguous_queries)} queries in {total_time:.3f}s (avg: {avg_time:.3f}s)")
        
        # Ambiguity detection should not significantly slow down processing
        assert avg_time < 0.2  # Should be fast even with ambiguity checking

    @pytest.mark.asyncio
    async def test_pattern_matching_performance(self, nlp_processor):
        """Test performance of regex pattern matching"""
        # Queries with many potential pattern matches
        pattern_heavy_queries = [
            "Find products priced at $10, $20, $30, $40, $50, $60, $70, $80, $90, $100",
            "Get reviews with 1 star, 2 stars, 3 stars, 4 stars, 5 stars ratings",
            "Extract data from last 1 day, 2 days, 3 days, 1 week, 2 weeks, 1 month",
            "Find first 10, 20, 30, 40, 50 items with quantities 1, 2, 3, 4, 5 each"
        ]

        times = []

        for query in pattern_heavy_queries:
            start_time = time.time()

            entities = await nlp_processor.extract_entities(query)

            end_time = time.time()
            processing_time = end_time - start_time
            times.append(processing_time)

            print(f"Pattern matching - {len(entities)} entities in {processing_time:.3f}s")

            # Should find entities quickly (some queries may have fewer matches)
            assert len(entities) >= 1  # At least one entity should be found
            assert processing_time < 0.5

        avg_time = sum(times) / len(times)
        print(f"Pattern matching average: {avg_time:.3f}s")
        assert avg_time < 0.3

    def test_scalability_stress_test(self, nlp_processor):
        """Stress test with many rapid queries"""
        # Generate many varied queries
        base_queries = [
            "get products under ${}",
            "find reviews with {} stars",
            "extract articles from {} days ago",
            "get jobs with ${} salary",
            "find {} items in stock"
        ]
        
        queries = []
        for i in range(200):  # 200 queries
            template = base_queries[i % len(base_queries)]
            value = (i % 100) + 1
            queries.append(template.format(value))
        
        start_time = time.time()
        
        for query in queries:
            result = asyncio.run(nlp_processor.process_command(
                query, 
                check_ambiguity=False
            ))
            assert "extraction_config" in result
        
        end_time = time.time()
        total_time = end_time - start_time
        queries_per_second = len(queries) / total_time
        
        print(f"Scalability test - {len(queries)} queries in {total_time:.3f}s ({queries_per_second:.1f} queries/sec)")
        
        # Should handle high query volume efficiently
        assert queries_per_second > 50  # Should process at least 50 queries per second
        assert total_time < 10  # Should complete 200 queries in under 10 seconds

    def test_cleanup_performance(self, nlp_processor):
        """Test performance of session cleanup operations"""
        # Create many old sessions
        for i in range(1000):
            session_id = f"old_session_{i}"
            nlp_processor.context_memory[session_id] = {
                "last_updated": "2020-01-01T00:00:00",  # Very old
                "conversation_history": [{"test": "data"}]
            }
        
        # Add some recent sessions
        for i in range(10):
            session_id = f"recent_session_{i}"
            nlp_processor.context_memory[session_id] = {
                "last_updated": datetime.now().isoformat(),
                "conversation_history": [{"test": "data"}]
            }
        
        print(f"Created {len(nlp_processor.context_memory)} sessions")
        
        # Test cleanup performance
        start_time = time.time()
        
        cleanup_result = nlp_processor.cleanup_old_sessions(max_age_hours=1)
        
        end_time = time.time()
        cleanup_time = end_time - start_time
        
        print(f"Cleanup performance - {cleanup_result['sessions_cleaned']} sessions cleaned in {cleanup_time:.3f}s")
        
        # Cleanup should be fast even with many sessions
        assert cleanup_time < 1.0  # Should complete in under 1 second
        assert cleanup_result["sessions_cleaned"] == 1000  # Should clean old sessions
        assert cleanup_result["sessions_kept"] == 10  # Should keep recent sessions


if __name__ == "__main__":
    pytest.main([__file__])
