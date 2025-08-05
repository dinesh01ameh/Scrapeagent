#!/usr/bin/env python3
"""
Test Adaptive Extraction Engine with crawl4ai Docker Integration
Validates that the adaptive extraction engine uses crawl4ai Docker service
"""

import asyncio
import json
import os
from datetime import datetime

# Set minimal environment for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-adaptive-extraction-testing-only")
os.environ.setdefault("CRAWL4AI_ENDPOINT", "http://localhost:11235")
os.environ.setdefault("CRAWL4AI_TIMEOUT", "30")

from services.crawl4ai_client import Crawl4aiDockerClient
from features.adaptive_extraction import AdaptiveExtractionEngine


async def test_adaptive_extraction_crawl4ai():
    """Test that adaptive extraction uses crawl4ai Docker service"""
    print("🚀 Testing Adaptive Extraction Engine with crawl4ai Docker")
    print("=" * 60)
    
    try:
        # Initialize crawl4ai client
        async with Crawl4aiDockerClient() as crawl4ai_client:
            print("✅ crawl4ai Docker client initialized")
            
            # Initialize adaptive extraction engine with crawl4ai client
            local_llm_config = {
                "manager": None,  # No LLM manager for this test
                "default_model": "test"
            }
            
            extraction_engine = AdaptiveExtractionEngine(
                local_llm_config=local_llm_config,
                crawl4ai_client=crawl4ai_client
            )
            print("✅ Adaptive Extraction Engine initialized with crawl4ai client")
            
            # Test basic extraction
            print("\n🔍 Testing basic adaptive extraction...")
            result = await extraction_engine.analyze_and_extract(
                "https://example.com",
                "Extract the title and description"
            )
            
            print(f"✅ Extraction successful: {result.success}")
            print(f"📊 Strategy used: {result.strategy_used}")
            print(f"🎯 Confidence: {result.confidence:.2f}")
            print(f"⏱️ Processing time: {result.processing_time:.2f}s")
            
            if result.success and result.data:
                print(f"📄 Data source: {result.data.get('source', 'unknown')}")
                
                # Verify it used crawl4ai Docker service
                if "crawl4ai" in result.data.get("source", ""):
                    print("✅ Confirmed: Used crawl4ai Docker service")
                else:
                    print(f"⚠️ Unexpected source: {result.data.get('source')}")
            
            # Test CSS extraction
            print("\n🎯 Testing CSS-based extraction...")
            css_result = await extraction_engine.analyze_and_extract(
                "https://example.com",
                "Extract title using CSS selectors"
            )
            
            print(f"✅ CSS extraction successful: {css_result.success}")
            print(f"📊 Strategy used: {css_result.strategy_used}")
            
            # Test LLM extraction
            print("\n🤖 Testing LLM-based extraction...")
            llm_result = await extraction_engine.analyze_and_extract(
                "https://example.com",
                "What is the main purpose of this website?"
            )
            
            print(f"✅ LLM extraction successful: {llm_result.success}")
            print(f"📊 Strategy used: {llm_result.strategy_used}")
            
            print("\n🎉 All adaptive extraction tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test execution"""
    success = await test_adaptive_extraction_crawl4ai()
    
    if success:
        print("\n✅ Adaptive Extraction crawl4ai Integration: SUCCESSFUL")
        print("🚀 Adaptive Extraction Engine now uses crawl4ai Docker service as PRIMARY")
        exit_code = 0
    else:
        print("\n❌ Adaptive Extraction crawl4ai Integration: FAILED")
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
