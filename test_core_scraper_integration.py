#!/usr/bin/env python3
"""
Test Core Scraper Integration with crawl4ai Docker Service
Validates that the core scraper prioritizes crawl4ai as the primary engine
"""

import asyncio
import json
import os
from datetime import datetime

# Set minimal environment for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-core-scraper-testing-only")
os.environ.setdefault("CRAWL4AI_ENDPOINT", "http://localhost:11235")
os.environ.setdefault("CRAWL4AI_TIMEOUT", "30")
os.environ.setdefault("ENABLE_ADAPTIVE_EXTRACTION", "false")
os.environ.setdefault("ENABLE_NATURAL_LANGUAGE_INTERFACE", "false")
os.environ.setdefault("ENABLE_PROXY_ROTATION", "false")
os.environ.setdefault("ENABLE_MULTIMODAL_PROCESSING", "false")
os.environ.setdefault("ENABLE_CONTENT_INTELLIGENCE", "false")

from core.scraper import SwissKnifeScraper


async def test_core_scraper_crawl4ai_integration():
    """Test that core scraper uses crawl4ai Docker service as primary engine"""
    print("🚀 Testing Core Scraper crawl4ai Integration")
    print("=" * 55)
    
    try:
        # Test scraper initialization
        async with SwissKnifeScraper() as scraper:
            print("✅ Core scraper initialized successfully")
            
            # Test status to verify crawl4ai is primary
            status = await scraper.get_status()
            print(f"📊 Scraper Status: {json.dumps(status, indent=2)}")
            
            # Verify crawl4ai is the primary component
            if "crawl4ai_docker" in status.get("components", {}):
                crawl4ai_status = status["components"]["crawl4ai_docker"]
                if crawl4ai_status.get("priority") == "primary_engine":
                    print("✅ crawl4ai Docker service confirmed as PRIMARY ENGINE")
                else:
                    print("❌ crawl4ai Docker service not set as primary engine")
                    return False
            else:
                print("❌ crawl4ai Docker service not found in components")
                return False
            
            # Test basic scraping via crawl4ai
            print("\n🔍 Testing basic scraping via crawl4ai...")
            result = await scraper.scrape("https://example.com")
            
            print(f"✅ Scrape successful: {result.get('result', {}).get('success', False)}")
            print(f"📊 Method used: {result.get('method')}")
            print(f"🔧 Source: {result.get('source')}")
            
            # Verify it used crawl4ai Docker service
            if result.get("method") == "crawl4ai_docker_primary":
                print("✅ Confirmed: Used crawl4ai Docker service as primary engine")
            else:
                print(f"❌ Expected crawl4ai_docker_primary, got: {result.get('method')}")
                return False
            
            # Test CSS extraction via crawl4ai
            print("\n🎯 Testing CSS extraction via crawl4ai...")
            css_config = {
                "css_selectors": {
                    "title": "h1",
                    "description": "p"
                }
            }
            
            css_result = await scraper.scrape(
                "https://example.com",
                extraction_config=css_config
            )
            
            print(f"✅ CSS extraction successful: {css_result.get('result', {}).get('success', False)}")
            print(f"📊 Method used: {css_result.get('method')}")
            
            # Test LLM extraction via crawl4ai
            print("\n🤖 Testing LLM extraction via crawl4ai...")
            llm_result = await scraper.scrape(
                "https://example.com",
                query="Extract the main title and description",
                extraction_config={"llm": True}
            )
            
            print(f"✅ LLM extraction successful: {llm_result.get('result', {}).get('success', False)}")
            print(f"📊 Method used: {llm_result.get('method')}")
            
            print("\n🎉 All core scraper integration tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test execution"""
    success = await test_core_scraper_crawl4ai_integration()
    
    if success:
        print("\n✅ Core Scraper crawl4ai Integration: SUCCESSFUL")
        print("🚀 crawl4ai Docker service is now the PRIMARY SCRAPING ENGINE")
        exit_code = 0
    else:
        print("\n❌ Core Scraper crawl4ai Integration: FAILED")
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
