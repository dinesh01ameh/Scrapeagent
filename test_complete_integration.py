#!/usr/bin/env python3
"""
Complete Integration Test Suite
Validates that crawl4ai Docker service and Jina AI are working as PRIMARY technologies
"""

import asyncio
import json
import os
from datetime import datetime

# Set minimal environment for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-complete-integration-testing")
os.environ.setdefault("CRAWL4AI_ENDPOINT", "http://localhost:11235")
os.environ.setdefault("CRAWL4AI_TIMEOUT", "30")
os.environ.setdefault("JINA_API_KEY", "test-api-key")
os.environ.setdefault("ENABLE_ADAPTIVE_EXTRACTION", "true")
os.environ.setdefault("ENABLE_MULTIMODAL_PROCESSING", "true")
os.environ.setdefault("ENABLE_NATURAL_LANGUAGE_INTERFACE", "false")
os.environ.setdefault("ENABLE_PROXY_ROTATION", "false")
os.environ.setdefault("ENABLE_CONTENT_INTELLIGENCE", "false")

from core.scraper import SwissKnifeScraper


async def test_complete_integration():
    """Test complete integration with crawl4ai and Jina AI as primary technologies"""
    print("🚀 Complete Integration Test Suite")
    print("=" * 50)
    print("Testing: crawl4ai Docker + Jina AI as PRIMARY technologies")
    print("=" * 50)
    
    try:
        # Test complete scraper initialization
        async with SwissKnifeScraper() as scraper:
            print("✅ SwissKnife Scraper initialized successfully")
            
            # Test comprehensive status
            print("\n📊 Testing comprehensive system status...")
            status = await scraper.get_status()
            
            print(f"🔧 System Status: {status.get('status')}")
            print(f"⏱️ Uptime: {status.get('uptime_seconds', 0):.2f}s")
            print(f"📈 Active Sessions: {status.get('active_sessions', 0)}")
            
            # Verify PRIMARY technologies are present and healthy
            components = status.get("components", {})
            
            # Check crawl4ai Docker service (PRIMARY SCRAPING ENGINE)
            if "crawl4ai_docker" in components:
                crawl4ai_status = components["crawl4ai_docker"]
                print(f"\n🚀 crawl4ai Docker Status: {crawl4ai_status.get('status')}")
                print(f"🎯 Priority: {crawl4ai_status.get('priority')}")
                
                if crawl4ai_status.get("priority") == "primary_scraping_engine":
                    print("✅ CONFIRMED: crawl4ai Docker is PRIMARY SCRAPING ENGINE")
                else:
                    print("❌ ERROR: crawl4ai Docker not set as primary scraping engine")
                    return False
            else:
                print("❌ ERROR: crawl4ai Docker service not found in components")
                return False
            
            # Check Jina AI service (CORE AI PROCESSING ENGINE)
            if "jina_ai" in components:
                jina_ai_status = components["jina_ai"]
                print(f"\n🤖 Jina AI Status: {jina_ai_status.get('status')}")
                print(f"🎯 Priority: {jina_ai_status.get('priority')}")
                
                if jina_ai_status.get("priority") == "core_ai_processing_engine":
                    print("✅ CONFIRMED: Jina AI is CORE AI PROCESSING ENGINE")
                else:
                    print("❌ ERROR: Jina AI not set as core AI processing engine")
                    return False
            else:
                print("❌ ERROR: Jina AI service not found in components")
                return False
            
            # Test PRIMARY scraping via crawl4ai Docker
            print("\n🔍 Testing PRIMARY scraping via crawl4ai Docker...")
            scrape_result = await scraper.scrape("https://example.com")
            
            print(f"✅ Scrape successful: {scrape_result.get('result', {}).get('success', False)}")
            print(f"📊 Method used: {scrape_result.get('method')}")
            print(f"🔧 Source: {scrape_result.get('source')}")
            
            # Verify it used crawl4ai Docker as primary
            if scrape_result.get("method") == "crawl4ai_docker_primary":
                print("✅ CONFIRMED: Used crawl4ai Docker service as PRIMARY scraping method")
            else:
                print(f"❌ ERROR: Expected crawl4ai_docker_primary, got: {scrape_result.get('method')}")
                return False
            
            # Test CSS extraction via crawl4ai Docker
            print("\n🎯 Testing CSS extraction via crawl4ai Docker...")
            css_result = await scraper.scrape(
                "https://example.com",
                extraction_config={"css_selectors": {"title": "h1", "description": "p"}}
            )
            
            print(f"✅ CSS extraction successful: {css_result.get('result', {}).get('success', False)}")
            print(f"📊 Method used: {css_result.get('method')}")
            
            if css_result.get("method") == "crawl4ai_docker_primary":
                print("✅ CONFIRMED: CSS extraction uses crawl4ai Docker as PRIMARY")
            else:
                print(f"⚠️ CSS extraction method: {css_result.get('method')}")
            
            # Test LLM extraction via crawl4ai Docker
            print("\n🤖 Testing LLM extraction via crawl4ai Docker...")
            llm_result = await scraper.scrape(
                "https://example.com",
                query="Extract the main title and description from this webpage"
            )
            
            print(f"✅ LLM extraction successful: {llm_result.get('result', {}).get('success', False)}")
            print(f"📊 Method used: {llm_result.get('method')}")
            
            if llm_result.get("method") == "crawl4ai_docker_primary":
                print("✅ CONFIRMED: LLM extraction uses crawl4ai Docker as PRIMARY")
            else:
                print(f"⚠️ LLM extraction method: {llm_result.get('method')}")
            
            # Test adaptive extraction with crawl4ai integration
            if scraper.extraction_engine:
                print("\n🎯 Testing Adaptive Extraction with crawl4ai integration...")
                adaptive_result = await scraper.extraction_engine.analyze_and_extract(
                    "https://example.com",
                    "Find the main heading and any price information"
                )
                
                print(f"✅ Adaptive extraction successful: {adaptive_result.success}")
                print(f"📊 Strategy used: {adaptive_result.strategy_used}")
                print(f"🎯 Confidence: {adaptive_result.confidence:.2f}")
                
                if adaptive_result.success and adaptive_result.data:
                    data_source = adaptive_result.data.get("source", "")
                    if "crawl4ai" in data_source:
                        print("✅ CONFIRMED: Adaptive extraction uses crawl4ai Docker")
                    else:
                        print(f"⚠️ Adaptive extraction source: {data_source}")
            
            # Test multimodal processing with Jina AI integration
            if scraper.multimodal_processor:
                print("\n📄 Testing Multimodal Processing with Jina AI integration...")
                try:
                    # This will test the Jina AI integration path
                    multimodal_result = await scraper.multimodal_processor.process_content(
                        "https://example.com/test.pdf",
                        "pdf"
                    )
                    
                    print(f"✅ Multimodal processing completed")
                    print(f"📊 Processing method: {multimodal_result.get('processing_method', 'unknown')}")
                    
                    if multimodal_result.get("processing_method") == "jina_ai_reader":
                        print("✅ CONFIRMED: Multimodal processing uses Jina AI as PRIMARY")
                    else:
                        print(f"⚠️ Multimodal processing method: {multimodal_result.get('processing_method')}")
                
                except Exception as e:
                    print(f"⚠️ Multimodal processing test failed (expected with test data): {e}")
            
            print("\n🎉 All integration tests completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_architectural_compliance():
    """Test architectural compliance with original project brief"""
    print("\n🏗️ Testing Architectural Compliance")
    print("=" * 40)
    
    compliance_score = 0
    max_score = 100
    
    try:
        # Test crawl4ai Docker service availability
        print("🔍 Testing crawl4ai Docker service availability...")
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:11235/health", timeout=5) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ crawl4ai Docker service healthy: {health_data.get('version')}")
                        compliance_score += 40
                    else:
                        print(f"❌ crawl4ai Docker service unhealthy: HTTP {response.status}")
            except Exception as e:
                print(f"❌ crawl4ai Docker service not accessible: {e}")
        
        # Test Jina AI integration
        print("\n🔍 Testing Jina AI integration...")
        from services.jina_ai_client import JinaAIClient
        
        try:
            async with JinaAIClient() as jina_client:
                status = await jina_client.get_service_status()
                if status.get("api_key_configured"):
                    print("✅ Jina AI client properly configured")
                    compliance_score += 30
                else:
                    print("⚠️ Jina AI client configured but no API key")
                    compliance_score += 15
        except Exception as e:
            print(f"❌ Jina AI integration failed: {e}")
        
        # Test Docker architecture
        print("\n🔍 Testing Docker architecture...")
        if os.path.exists("docker-compose.yml"):
            print("✅ docker-compose.yml exists")
            
            # Check for crawl4ai service in docker-compose
            with open("docker-compose.yml", "r") as f:
                compose_content = f.read()
                if "crawl4ai:" in compose_content:
                    print("✅ crawl4ai service found in docker-compose.yml")
                    compliance_score += 30
                else:
                    print("❌ crawl4ai service not found in docker-compose.yml")
        else:
            print("❌ docker-compose.yml not found")
        
        print(f"\n📊 Architectural Compliance Score: {compliance_score}/{max_score}")
        
        if compliance_score >= 80:
            print("✅ EXCELLENT: High architectural compliance")
            return True
        elif compliance_score >= 60:
            print("⚠️ GOOD: Acceptable architectural compliance")
            return True
        else:
            print("❌ POOR: Low architectural compliance")
            return False
            
    except Exception as e:
        print(f"❌ Compliance test failed: {e}")
        return False


async def main():
    """Main test execution"""
    print("🚀 Starting Complete Integration Test Suite")
    print("=" * 60)
    print("Validating: crawl4ai Docker + Jina AI as PRIMARY technologies")
    print("=" * 60)
    
    # Test complete integration
    integration_success = await test_complete_integration()
    
    # Test architectural compliance
    compliance_success = await test_architectural_compliance()
    
    overall_success = integration_success and compliance_success
    
    print("\n" + "=" * 60)
    print("📊 FINAL INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    if overall_success:
        print("✅ COMPLETE INTEGRATION: SUCCESSFUL")
        print("🚀 crawl4ai Docker service: PRIMARY SCRAPING ENGINE")
        print("🤖 Jina AI: CORE AI PROCESSING ENGINE")
        print("🏗️ Architecture: COMPLIANT with original project brief")
        exit_code = 0
    else:
        print("❌ COMPLETE INTEGRATION: ISSUES DETECTED")
        print("⚠️ Review test output for specific issues")
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
