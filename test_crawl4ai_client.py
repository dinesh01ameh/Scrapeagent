#!/usr/bin/env python3
"""
Test crawl4ai Docker Client Integration
Validates the new crawl4ai Docker client service
"""

import asyncio
import json
import os
from datetime import datetime

# Set minimal environment for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-crawl4ai-client-testing-only")
os.environ.setdefault("CRAWL4AI_ENDPOINT", "http://localhost:11235")
os.environ.setdefault("CRAWL4AI_TIMEOUT", "30")

from services.crawl4ai_client import Crawl4aiDockerClient


async def test_crawl4ai_client():
    """Test the crawl4ai Docker client"""
    print("🚀 Testing crawl4ai Docker Client Integration")
    print("=" * 50)
    
    try:
        # Test basic crawling
        async with Crawl4aiDockerClient() as client:
            print("✅ Client initialized successfully")
            
            # Test service info
            service_info = await client.get_service_info()
            print(f"📊 Service Info: {service_info}")
            
            # Test single URL crawl
            print("\n🔍 Testing single URL crawl...")
            result = await client.crawl_url("https://example.com")
            
            print(f"✅ Crawl successful: {result['success']}")
            print(f"📄 Content length: {len(result.get('html', ''))}")
            print(f"📝 Markdown length: {len(result.get('markdown', ''))}")
            print(f"⏱️ Processing time: {result.get('processing_time', 0)}s")
            
            # Test CSS extraction
            print("\n🎯 Testing CSS extraction...")
            css_result = await client.extract_with_css(
                "https://example.com",
                {"title": "h1", "description": "p"}
            )
            
            print(f"✅ CSS extraction successful: {css_result['success']}")
            if css_result.get('extracted_content'):
                print(f"📊 Extracted data: {css_result['extracted_content']}")
            
            print("\n🎉 All tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def main():
    """Main test execution"""
    success = await test_crawl4ai_client()
    
    if success:
        print("\n✅ crawl4ai Docker Client Integration: SUCCESSFUL")
        exit_code = 0
    else:
        print("\n❌ crawl4ai Docker Client Integration: FAILED")
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
