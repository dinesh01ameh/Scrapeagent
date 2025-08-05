#!/usr/bin/env python3
"""
Smart Scraper AI - Core Integration Audit Script
Verifies original architecture components and their current status
"""

import asyncio
import aiohttp
import subprocess
import sys
import json
import os
from typing import Dict, Any, List
from datetime import datetime
import importlib.util


class CoreIntegrationAuditor:
    """Audits core Smart Scraper AI integrations"""
    
    def __init__(self):
        self.results = {
            "audit_timestamp": datetime.now().isoformat(),
            "crawl4ai_status": {},
            "jina_ai_status": {},
            "docker_services": {},
            "dependencies": {},
            "architecture_compliance": {}
        }
    
    async def audit_crawl4ai_integration(self) -> Dict[str, Any]:
        """Check if crawl4ai is properly integrated"""
        print("🔍 Auditing crawl4ai integration...")
        
        # Check if crawl4ai is installed
        try:
            import crawl4ai
            # Try to get version safely
            try:
                if hasattr(crawl4ai, '__version__'):
                    version = crawl4ai.__version__
                    if hasattr(version, '__version__'):
                        crawl4ai_version = version.__version__
                    else:
                        crawl4ai_version = str(version)
                else:
                    crawl4ai_version = 'unknown'
            except:
                crawl4ai_version = 'unknown'

            self.results["crawl4ai_status"]["installed"] = True
            self.results["crawl4ai_status"]["version"] = crawl4ai_version
            print(f"✅ crawl4ai installed: v{crawl4ai_version}")
        except ImportError:
            self.results["crawl4ai_status"]["installed"] = False
            print("❌ crawl4ai not installed")
            return self.results["crawl4ai_status"]
        
        # Check for crawl4ai Docker service
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:11235/health', timeout=5) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        self.results["crawl4ai_status"]["docker_service"] = {
                            "active": True,
                            "health": health_data
                        }
                        print("✅ crawl4ai Docker service is active")
                    else:
                        self.results["crawl4ai_status"]["docker_service"] = {
                            "active": False,
                            "status_code": response.status
                        }
                        print(f"⚠️ crawl4ai Docker service responded with status {response.status}")
        except Exception as e:
            self.results["crawl4ai_status"]["docker_service"] = {
                "active": False,
                "error": str(e)
            }
            print(f"❌ crawl4ai Docker service not accessible: {e}")
        
        # Check for crawl4ai usage in source code
        crawl4ai_usage = self._scan_for_crawl4ai_usage()
        self.results["crawl4ai_status"]["source_usage"] = crawl4ai_usage
        
        return self.results["crawl4ai_status"]
    
    async def audit_jina_ai_integration(self) -> Dict[str, Any]:
        """Check if Jina AI APIs are integrated"""
        print("🔍 Auditing Jina AI integration...")
        
        # Check if jina is installed
        try:
            import jina
            # Try to get version safely
            try:
                jina_version = str(getattr(jina, '__version__', 'unknown'))
            except:
                jina_version = 'unknown'

            self.results["jina_ai_status"]["installed"] = True
            self.results["jina_ai_status"]["version"] = jina_version
            print(f"✅ jina installed: v{jina_version}")
        except ImportError:
            self.results["jina_ai_status"]["installed"] = False
            print("❌ jina not installed")
        
        # Check for Jina API endpoints in configuration
        jina_config = self._check_jina_configuration()
        self.results["jina_ai_status"]["configuration"] = jina_config
        
        # Check for Jina API usage in source code
        jina_usage = self._scan_for_jina_usage()
        self.results["jina_ai_status"]["source_usage"] = jina_usage
        
        # Test Jina Reader API if configured
        if jina_config.get("api_key"):
            reader_test = await self._test_jina_reader_api(jina_config)
            self.results["jina_ai_status"]["api_test"] = reader_test
        
        return self.results["jina_ai_status"]
    
    def audit_docker_services(self) -> Dict[str, Any]:
        """Check Docker services status"""
        print("🔍 Auditing Docker services...")
        
        try:
            # Check if docker-compose.yml exists
            if os.path.exists("docker-compose.yml"):
                self.results["docker_services"]["compose_file"] = True
                print("✅ docker-compose.yml found")
                
                # Parse docker-compose.yml for services
                services = self._parse_docker_compose()
                self.results["docker_services"]["services"] = services
                
            else:
                self.results["docker_services"]["compose_file"] = False
                print("❌ docker-compose.yml not found")
        
        except Exception as e:
            self.results["docker_services"]["error"] = str(e)
            print(f"❌ Error auditing Docker services: {e}")
        
        return self.results["docker_services"]
    
    def audit_dependencies(self) -> Dict[str, Any]:
        """Check dependency status"""
        print("🔍 Auditing dependencies...")
        
        # Check requirements.txt
        if os.path.exists("requirements.txt"):
            deps = self._parse_requirements("requirements.txt")
            self.results["dependencies"]["requirements"] = deps
            print(f"✅ Found {len(deps)} dependencies in requirements.txt")
        
        # Check pyproject.toml
        if os.path.exists("pyproject.toml"):
            pyproject_deps = self._parse_pyproject_dependencies()
            self.results["dependencies"]["pyproject"] = pyproject_deps
            print(f"✅ Found pyproject.toml dependencies")
        
        return self.results["dependencies"]
    
    def _scan_for_crawl4ai_usage(self) -> Dict[str, Any]:
        """Scan source code for crawl4ai usage"""
        usage = {
            "imports_found": [],
            "files_with_usage": [],
            "docker_client_usage": False
        }
        
        # Scan Python files for crawl4ai imports
        for root, dirs, files in os.walk("."):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            if 'crawl4ai' in content:
                                usage["files_with_usage"].append(file_path)
                                
                                # Check for specific imports
                                if 'from crawl4ai import' in content or 'import crawl4ai' in content:
                                    usage["imports_found"].append(file_path)
                                
                                # Check for Docker client usage
                                if 'Crawl4aiDockerClient' in content:
                                    usage["docker_client_usage"] = True
                    
                    except Exception:
                        continue  # Skip files that can't be read
        
        return usage
    
    def _scan_for_jina_usage(self) -> Dict[str, Any]:
        """Scan source code for Jina AI usage"""
        usage = {
            "api_endpoints": [],
            "files_with_usage": [],
            "reader_api_usage": False,
            "search_api_usage": False
        }
        
        jina_endpoints = [
            "https://r.jina.ai",
            "https://s.jina.ai",
            "api.jina.ai"
        ]
        
        # Scan Python files for Jina usage
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Check for Jina endpoints
                            for endpoint in jina_endpoints:
                                if endpoint in content:
                                    usage["files_with_usage"].append(file_path)
                                    usage["api_endpoints"].append(endpoint)
                                    
                                    if "r.jina.ai" in content:
                                        usage["reader_api_usage"] = True
                                    if "s.jina.ai" in content:
                                        usage["search_api_usage"] = True
                    
                    except Exception:
                        continue
        
        return usage
    
    def _check_jina_configuration(self) -> Dict[str, Any]:
        """Check Jina configuration in settings"""
        config = {}
        
        # Check environment variables
        config["api_key"] = os.getenv("JINA_API_KEY")
        config["reader_endpoint"] = os.getenv("JINA_READER_ENDPOINT", "https://r.jina.ai")
        
        # Check settings file
        try:
            if os.path.exists("config/settings.py"):
                with open("config/settings.py", 'r') as f:
                    content = f.read()
                    if "JINA_API_KEY" in content:
                        config["settings_file_configured"] = True
                    else:
                        config["settings_file_configured"] = False
        except Exception:
            config["settings_file_configured"] = False
        
        return config
    
    async def _test_jina_reader_api(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Jina Reader API connectivity"""
        try:
            endpoint = config.get("reader_endpoint", "https://r.jina.ai")
            api_key = config.get("api_key")
            
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            async with aiohttp.ClientSession() as session:
                test_url = f"{endpoint}/https://example.com"
                async with session.get(test_url, headers=headers, timeout=10) as response:
                    return {
                        "accessible": response.status == 200,
                        "status_code": response.status,
                        "test_url": test_url
                    }
        except Exception as e:
            return {
                "accessible": False,
                "error": str(e)
            }
    
    def _parse_docker_compose(self) -> Dict[str, Any]:
        """Parse docker-compose.yml for service information"""
        services = {}
        try:
            import yaml
            with open("docker-compose.yml", 'r') as f:
                compose_data = yaml.safe_load(f)
                
                if "services" in compose_data:
                    for service_name, service_config in compose_data["services"].items():
                        services[service_name] = {
                            "image": service_config.get("image"),
                            "ports": service_config.get("ports", []),
                            "depends_on": service_config.get("depends_on", [])
                        }
        except Exception as e:
            services["error"] = str(e)
        
        return services
    
    def _parse_requirements(self, file_path: str) -> List[str]:
        """Parse requirements.txt file"""
        deps = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        deps.append(line)
        except Exception:
            pass
        return deps
    
    def _parse_pyproject_dependencies(self) -> Dict[str, Any]:
        """Parse pyproject.toml dependencies"""
        try:
            import tomli
            with open("pyproject.toml", 'rb') as f:
                data = tomli.load(f)
                return {
                    "dependencies": data.get("project", {}).get("dependencies", []),
                    "optional_dependencies": data.get("project", {}).get("optional-dependencies", {})
                }
        except Exception as e:
            return {"error": str(e)}
    
    async def run_full_audit(self) -> Dict[str, Any]:
        """Run complete audit of core integrations"""
        print("🚀 Starting Smart Scraper AI Core Integration Audit")
        print("=" * 60)
        
        # Run all audits
        await self.audit_crawl4ai_integration()
        await self.audit_jina_ai_integration()
        self.audit_docker_services()
        self.audit_dependencies()
        
        # Generate compliance report
        self._generate_compliance_report()
        
        print("\n" + "=" * 60)
        print("📊 Audit Complete!")
        
        return self.results
    
    def _generate_compliance_report(self):
        """Generate architecture compliance report"""
        compliance = {
            "crawl4ai_compliant": False,
            "jina_ai_compliant": False,
            "docker_architecture_compliant": False,
            "overall_compliance_score": 0
        }
        
        # Check crawl4ai compliance
        crawl4ai_status = self.results["crawl4ai_status"]
        if (crawl4ai_status.get("installed") and 
            len(crawl4ai_status.get("source_usage", {}).get("imports_found", [])) > 0):
            compliance["crawl4ai_compliant"] = True
        
        # Check Jina AI compliance
        jina_status = self.results["jina_ai_status"]
        if (jina_status.get("installed") and 
            (jina_status.get("source_usage", {}).get("reader_api_usage") or
             jina_status.get("source_usage", {}).get("search_api_usage"))):
            compliance["jina_ai_compliant"] = True
        
        # Check Docker architecture compliance
        docker_services = self.results["docker_services"]
        if docker_services.get("compose_file") and len(docker_services.get("services", {})) > 0:
            compliance["docker_architecture_compliant"] = True
        
        # Calculate overall compliance score
        score = 0
        if compliance["crawl4ai_compliant"]:
            score += 40
        if compliance["jina_ai_compliant"]:
            score += 30
        if compliance["docker_architecture_compliant"]:
            score += 30
        
        compliance["overall_compliance_score"] = score
        self.results["architecture_compliance"] = compliance


async def main():
    """Main audit execution"""
    auditor = CoreIntegrationAuditor()
    results = await auditor.run_full_audit()
    
    # Save results to file
    with open("audit_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: audit_results.json")
    
    # Print summary
    compliance = results["architecture_compliance"]
    print(f"\n📈 COMPLIANCE SUMMARY:")
    print(f"   crawl4ai Integration: {'✅' if compliance['crawl4ai_compliant'] else '❌'}")
    print(f"   Jina AI Integration:  {'✅' if compliance['jina_ai_compliant'] else '❌'}")
    print(f"   Docker Architecture:  {'✅' if compliance['docker_architecture_compliant'] else '❌'}")
    print(f"   Overall Score: {compliance['overall_compliance_score']}/100")


if __name__ == "__main__":
    asyncio.run(main())
