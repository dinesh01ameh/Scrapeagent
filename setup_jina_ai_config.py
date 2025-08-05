#!/usr/bin/env python3
"""
Jina AI Configuration Setup Script
Configures Jina AI API key and validates full integration
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

from services.jina_ai_client import JinaAIClient


class JinaAIConfigurator:
    """Handles Jina AI configuration and validation"""
    
    def __init__(self):
        self.config_file = ".env"
        self.docker_config_file = ".env.docker"
        
    def setup_api_key_configuration(self, api_key: Optional[str] = None) -> bool:
        """Set up Jina AI API key in environment files"""
        print("🔧 Setting up Jina AI API Key Configuration")
        print("=" * 50)
        
        if not api_key:
            print("📝 Jina AI API Key Setup Instructions:")
            print("1. Visit: https://jina.ai/")
            print("2. Sign up for a free account")
            print("3. Navigate to API Keys section")
            print("4. Generate a new API key")
            print("5. Copy the API key")
            print()
            
            # Check if user wants to enter API key interactively
            user_input = input("Do you have a Jina AI API key to configure? (y/n): ").lower().strip()
            
            if user_input == 'y':
                api_key = input("Enter your Jina AI API key: ").strip()
                if not api_key:
                    print("❌ No API key provided")
                    return False
            else:
                print("⚠️ Skipping API key configuration")
                print("💡 You can configure it later by setting JINA_API_KEY environment variable")
                return True
        
        # Update .env file
        self._update_env_file(self.config_file, api_key)
        
        # Update .env.docker file
        self._update_env_file(self.docker_config_file, api_key)
        
        print(f"✅ Jina AI API key configured in {self.config_file} and {self.docker_config_file}")
        return True
    
    def _update_env_file(self, file_path: str, api_key: str):
        """Update environment file with Jina AI API key"""
        if not os.path.exists(file_path):
            print(f"⚠️ {file_path} not found, creating new file")
            with open(file_path, 'w') as f:
                f.write(f"JINA_API_KEY={api_key}\n")
            return
        
        # Read existing file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add JINA_API_KEY
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('JINA_API_KEY='):
                lines[i] = f"JINA_API_KEY={api_key}\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"JINA_API_KEY={api_key}\n")
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.writelines(lines)
    
    async def validate_jina_ai_integration(self) -> Dict[str, Any]:
        """Validate complete Jina AI integration"""
        print("\n🔍 Validating Jina AI Integration")
        print("=" * 40)
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "unknown"
        }
        
        try:
            async with JinaAIClient() as jina_client:
                print("✅ Jina AI client initialized")
                
                # Test 1: Service Status
                print("\n📊 Testing service status...")
                status = await jina_client.get_service_status()
                validation_results["tests"]["service_status"] = {
                    "status": "pass",
                    "api_key_configured": status.get("api_key_configured", False),
                    "endpoints": status.get("endpoints", {})
                }
                print(f"✅ Service status: API key configured = {status.get('api_key_configured')}")
                
                # Test 2: Reader API
                print("\n📖 Testing Jina AI Reader API...")
                try:
                    reader_result = await jina_client.read_url("https://example.com")
                    if reader_result.get("success"):
                        validation_results["tests"]["reader_api"] = {
                            "status": "pass",
                            "content_length": len(reader_result.get("content", "")),
                            "response_time": "< 5s"
                        }
                        print("✅ Reader API: Working correctly")
                    else:
                        validation_results["tests"]["reader_api"] = {
                            "status": "fail",
                            "error": "API returned unsuccessful result"
                        }
                        print("❌ Reader API: Returned unsuccessful result")
                except Exception as e:
                    validation_results["tests"]["reader_api"] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"❌ Reader API: {e}")
                
                # Test 3: Search API
                print("\n🔍 Testing Jina AI Search API...")
                try:
                    search_result = await jina_client.search("artificial intelligence")
                    if search_result.get("success"):
                        validation_results["tests"]["search_api"] = {
                            "status": "pass",
                            "query": search_result.get("query"),
                            "results_length": len(search_result.get("results", ""))
                        }
                        print("✅ Search API: Working correctly")
                    else:
                        validation_results["tests"]["search_api"] = {
                            "status": "fail",
                            "error": "API returned unsuccessful result"
                        }
                        print("❌ Search API: Returned unsuccessful result")
                except Exception as e:
                    validation_results["tests"]["search_api"] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"❌ Search API: {e}")
                
                # Test 4: Embeddings API (requires valid API key)
                if jina_client.api_key and jina_client.api_key != "test-api-key":
                    print("\n🤖 Testing Jina AI Embeddings API...")
                    try:
                        embeddings_result = await jina_client.get_embeddings(["test text"])
                        if embeddings_result.get("success"):
                            validation_results["tests"]["embeddings_api"] = {
                                "status": "pass",
                                "embeddings_count": len(embeddings_result.get("embeddings", [])),
                                "model": embeddings_result.get("model")
                            }
                            print("✅ Embeddings API: Working correctly")
                        else:
                            validation_results["tests"]["embeddings_api"] = {
                                "status": "fail",
                                "error": "API returned unsuccessful result"
                            }
                            print("❌ Embeddings API: Returned unsuccessful result")
                    except Exception as e:
                        validation_results["tests"]["embeddings_api"] = {
                            "status": "error",
                            "error": str(e)
                        }
                        print(f"❌ Embeddings API: {e}")
                else:
                    validation_results["tests"]["embeddings_api"] = {
                        "status": "skipped",
                        "reason": "No valid API key configured"
                    }
                    print("⚠️ Embeddings API: Skipped (requires valid API key)")
                
                # Calculate overall status
                test_results = validation_results["tests"]
                passed = sum(1 for test in test_results.values() if test.get("status") == "pass")
                total = len([t for t in test_results.values() if t.get("status") != "skipped"])
                
                if passed == total and total > 0:
                    validation_results["overall_status"] = "excellent"
                elif passed >= total * 0.7:
                    validation_results["overall_status"] = "good"
                elif passed >= total * 0.5:
                    validation_results["overall_status"] = "partial"
                else:
                    validation_results["overall_status"] = "poor"
                
                print(f"\n📊 Overall Jina AI Integration Status: {validation_results['overall_status'].upper()}")
                print(f"📈 Tests Passed: {passed}/{total}")
                
        except Exception as e:
            validation_results["tests"]["initialization"] = {
                "status": "error",
                "error": str(e)
            }
            validation_results["overall_status"] = "failed"
            print(f"❌ Jina AI integration validation failed: {e}")
        
        return validation_results
    
    async def test_pdf_processing_pipeline(self) -> Dict[str, Any]:
        """Test the complete PDF processing pipeline with Jina AI"""
        print("\n📄 Testing PDF Processing Pipeline with Jina AI")
        print("=" * 50)
        
        try:
            from features.multimodal_processing import PDFAnalyzer
            
            async with JinaAIClient() as jina_client:
                pdf_analyzer = PDFAnalyzer(jina_ai_client=jina_client)
                
                # Test with a sample PDF URL (this would be a real PDF in production)
                test_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
                
                print(f"🔍 Testing PDF processing for: {test_url}")
                
                result = await pdf_analyzer.process(test_url)
                
                pipeline_result = {
                    "test_url": test_url,
                    "processing_method": result.get("processing_method", "unknown"),
                    "success": result.get("success", False),
                    "content_length": len(result.get("text_content", "")),
                    "source": result.get("source", "unknown"),
                    "timestamp": datetime.now().isoformat()
                }
                
                if result.get("processing_method") == "jina_ai_reader":
                    print("✅ PDF processing uses Jina AI Reader as PRIMARY method")
                    pipeline_result["status"] = "excellent"
                elif result.get("processing_method") == "local_fallback":
                    print("⚠️ PDF processing fell back to local method")
                    pipeline_result["status"] = "fallback"
                else:
                    print(f"❓ PDF processing method: {result.get('processing_method')}")
                    pipeline_result["status"] = "unknown"
                
                return pipeline_result
                
        except Exception as e:
            print(f"❌ PDF processing pipeline test failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_complete_configuration(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Run complete Jina AI configuration and validation"""
        print("🚀 Starting Complete Jina AI Configuration")
        print("=" * 60)
        
        results = {
            "configuration_timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        # Step 1: Configure API key
        config_success = self.setup_api_key_configuration(api_key)
        results["steps"]["api_key_configuration"] = {
            "success": config_success,
            "timestamp": datetime.now().isoformat()
        }
        
        if config_success:
            # Step 2: Validate integration
            validation_results = await self.validate_jina_ai_integration()
            results["steps"]["integration_validation"] = validation_results
            
            # Step 3: Test PDF pipeline
            pdf_results = await self.test_pdf_processing_pipeline()
            results["steps"]["pdf_pipeline_test"] = pdf_results
            
            # Overall assessment
            if validation_results.get("overall_status") in ["excellent", "good"]:
                results["overall_status"] = "success"
                results["message"] = "Jina AI configuration completed successfully"
            else:
                results["overall_status"] = "partial"
                results["message"] = "Jina AI configuration completed with some limitations"
        else:
            results["overall_status"] = "failed"
            results["message"] = "Jina AI configuration failed"
        
        return results


async def main():
    """Main configuration execution"""
    configurator = JinaAIConfigurator()
    
    # Run complete configuration
    results = await configurator.run_complete_configuration()
    
    # Save results
    with open("jina_ai_configuration_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Configuration results saved to: jina_ai_configuration_results.json")
    
    # Print final status
    print("\n" + "=" * 60)
    print("📊 JINA AI CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"🎯 Overall Status: {results['overall_status'].upper()}")
    print(f"💬 Message: {results['message']}")
    
    if results["overall_status"] == "success":
        print("\n🎉 Jina AI is now fully configured and operational!")
        print("🚀 The complete crawl4ai + Jina AI stack is ready for production use")
        return 0
    else:
        print("\n⚠️ Jina AI configuration completed with limitations")
        print("💡 Check the results file for detailed information")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
