#!/usr/bin/env python3
"""
Smart Scraper AI - crawl4ai Docker Service Integration Test
Verifies that the crawl4ai Docker service is properly integrated and functional
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any
from datetime import datetime


class Crawl4aiIntegrationTester:
    """Tests crawl4ai Docker service integration"""
    
    def __init__(self, base_url: str = "http://localhost:11235"):
        self.base_url = base_url
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "tests": {}
        }
    
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test crawl4ai health endpoint"""
        print("🔍 Testing crawl4ai health endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=10) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        result = {
                            "status": "PASS",
                            "response_code": response.status,
                            "health_data": health_data
                        }
                        print("✅ Health endpoint responding correctly")
                    else:
                        result = {
                            "status": "FAIL",
                            "response_code": response.status,
                            "error": f"Unexpected status code: {response.status}"
                        }
                        print(f"❌ Health endpoint failed with status {response.status}")
        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Health endpoint test failed: {e}")
        
        self.results["tests"]["health_endpoint"] = result
        return result
    
    async def test_basic_crawl(self) -> Dict[str, Any]:
        """Test basic crawling functionality"""
        print("🔍 Testing basic crawl functionality...")
        
        payload = {
            "urls": ["https://example.com"],
            "crawler_config": {
                "headless": True,
                "cache_mode": "BYPASS"
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/crawl",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        crawl_data = await response.json()
                        
                        # Validate response structure
                        if "results" in crawl_data and len(crawl_data["results"]) > 0:
                            first_result = crawl_data["results"][0]
                            success = first_result.get("success", False)
                            
                            result = {
                                "status": "PASS" if success else "PARTIAL",
                                "response_code": response.status,
                                "crawl_success": success,
                                "url_crawled": first_result.get("url"),
                                "content_length": len(first_result.get("markdown", "")),
                                "has_html": bool(first_result.get("html")),
                                "has_markdown": bool(first_result.get("markdown"))
                            }
                            
                            if success:
                                print("✅ Basic crawl successful")
                            else:
                                print("⚠️ Crawl completed but with issues")
                        else:
                            result = {
                                "status": "FAIL",
                                "response_code": response.status,
                                "error": "Invalid response structure"
                            }
                            print("❌ Invalid crawl response structure")
                    else:
                        result = {
                            "status": "FAIL",
                            "response_code": response.status,
                            "error": f"Crawl request failed with status {response.status}"
                        }
                        print(f"❌ Crawl request failed with status {response.status}")
        
        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Basic crawl test failed: {e}")
        
        self.results["tests"]["basic_crawl"] = result
        return result
    
    async def test_api_schema(self) -> Dict[str, Any]:
        """Test API schema endpoint"""
        print("🔍 Testing API schema endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/schema", timeout=10) as response:
                    if response.status == 200:
                        schema_data = await response.json()
                        result = {
                            "status": "PASS",
                            "response_code": response.status,
                            "has_openapi": "openapi" in schema_data,
                            "has_paths": "paths" in schema_data,
                            "api_version": schema_data.get("info", {}).get("version")
                        }
                        print("✅ API schema endpoint working")
                    else:
                        result = {
                            "status": "FAIL",
                            "response_code": response.status,
                            "error": f"Schema endpoint failed with status {response.status}"
                        }
                        print(f"❌ Schema endpoint failed with status {response.status}")
        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e)
            }
            print(f"❌ Schema endpoint test failed: {e}")
        
        self.results["tests"]["api_schema"] = result
        return result
    
    async def test_docker_client_compatibility(self) -> Dict[str, Any]:
        """Test crawl4ai Docker client compatibility"""
        print("🔍 Testing crawl4ai Docker client compatibility...")
        
        try:
            # Try to import and test crawl4ai Docker client
            from crawl4ai.docker_client import Crawl4aiDockerClient
            from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode
            
            async with Crawl4aiDockerClient(base_url=self.base_url) as client:
                results = await client.crawl(
                    ["https://example.com"],
                    browser_config=BrowserConfig(headless=True),
                    crawler_config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
                )
                
                if results and len(results) > 0:
                    first_result = results[0]
                    result = {
                        "status": "PASS",
                        "client_compatible": True,
                        "crawl_success": first_result.success,
                        "content_length": len(first_result.markdown) if first_result.markdown else 0
                    }
                    print("✅ Docker client compatibility confirmed")
                else:
                    result = {
                        "status": "FAIL",
                        "client_compatible": True,
                        "error": "No results returned from Docker client"
                    }
                    print("❌ Docker client returned no results")
        
        except ImportError as e:
            result = {
                "status": "SKIP",
                "client_compatible": False,
                "error": f"crawl4ai Docker client not available: {e}"
            }
            print(f"⚠️ Skipping Docker client test: {e}")
        
        except Exception as e:
            result = {
                "status": "FAIL",
                "client_compatible": False,
                "error": str(e)
            }
            print(f"❌ Docker client test failed: {e}")
        
        self.results["tests"]["docker_client"] = result
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🚀 Starting crawl4ai Docker Service Integration Tests")
        print("=" * 60)
        
        # Run all tests
        await self.test_health_endpoint()
        await self.test_api_schema()
        await self.test_basic_crawl()
        await self.test_docker_client_compatibility()
        
        # Calculate overall status
        test_results = self.results["tests"]
        passed = sum(1 for test in test_results.values() if test.get("status") == "PASS")
        failed = sum(1 for test in test_results.values() if test.get("status") == "FAIL")
        skipped = sum(1 for test in test_results.values() if test.get("status") == "SKIP")
        total = len(test_results)
        
        self.results["summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": (passed / (total - skipped)) * 100 if (total - skipped) > 0 else 0,
            "overall_status": "PASS" if failed == 0 else "FAIL"
        }
        
        print("\n" + "=" * 60)
        print("📊 Integration Test Results:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Skipped: {skipped}")
        print(f"   Success Rate: {self.results['summary']['success_rate']:.1f}%")
        print(f"   Overall Status: {self.results['summary']['overall_status']}")
        
        return self.results


async def main():
    """Main test execution"""
    tester = Crawl4aiIntegrationTester()
    results = await tester.run_all_tests()
    
    # Save results
    with open("crawl4ai_integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: crawl4ai_integration_test_results.json")
    
    # Exit with appropriate code
    exit_code = 0 if results["summary"]["overall_status"] == "PASS" else 1
    print(f"\n🎯 Test execution complete. Exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
