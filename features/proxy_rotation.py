"""
Advanced Proxy Rotation System with Health Monitoring and Optimization
"""

import asyncio
import aiohttp
import random
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
import json
import statistics

from utils.exceptions import ProxyError, ProxyValidationError
from utils.logging import LoggingMixin


class ProxyMetrics:
    """Track proxy performance metrics"""

    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.last_success = None
        self.last_failure = None
        self.consecutive_failures = 0
        self.created_at = datetime.now()

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times[-100:])  # Last 100 requests

    @property
    def health_score(self) -> float:
        """Calculate overall health score (0.0 to 1.0)"""
        # Base score from success rate
        base_score = self.success_rate

        # Penalty for consecutive failures
        failure_penalty = min(self.consecutive_failures * 0.1, 0.5)

        # Bonus for recent success
        recency_bonus = 0.0
        if self.last_success:
            hours_since_success = (datetime.now() - self.last_success).total_seconds() / 3600
            if hours_since_success < 1:
                recency_bonus = 0.1

        # Response time factor (faster is better)
        speed_factor = 1.0
        if self.average_response_time > 0:
            speed_factor = max(0.5, 1.0 - (self.average_response_time / 10.0))

        final_score = (base_score - failure_penalty + recency_bonus) * speed_factor
        return max(0.0, min(1.0, final_score))

    def record_success(self, response_time: float):
        """Record a successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.response_times.append(response_time)
        self.last_success = datetime.now()
        self.consecutive_failures = 0

        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

    def record_failure(self):
        """Record a failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_failure = datetime.now()
        self.consecutive_failures += 1


class AdvancedProxyManager(LoggingMixin):
    """
    Intelligent proxy rotation with health monitoring and optimization
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}

        # Proxy pools organized by type
        self.proxy_pools = {
            "residential": [],
            "datacenter": [],
            "mobile": [],
            "free": []
        }

        # Metrics tracking
        self.proxy_metrics: Dict[str, ProxyMetrics] = {}

        # Rotation state
        self.rotation_indices = {pool: 0 for pool in self.proxy_pools.keys()}

        # Health monitoring
        self.health_monitor_task = None
        self.monitoring_active = False

        # Configuration
        self.health_check_interval = self.config.get("health_check_interval", 300)  # 5 minutes
        self.max_consecutive_failures = self.config.get("max_consecutive_failures", 5)
        self.min_health_score = self.config.get("min_health_score", 0.3)
        self.validation_timeout = self.config.get("validation_timeout", 10)

        # Rotation strategies
        self.rotation_strategies = {
            "round_robin": self._round_robin_rotation,
            "least_used": self._least_used_rotation,
            "failure_aware": self._failure_aware_rotation,
            "geographic": self._geographic_rotation,
            "random": self._random_rotation,
            "fastest": self._fastest_rotation
        }

        self.logger.info("AdvancedProxyManager initialized")

    async def initialize(self):
        """Initialize the proxy manager"""
        self.logger.info("Initializing proxy manager...")

        # Start health monitoring
        await self.start_health_monitoring()

        self.logger.info("Proxy manager initialized successfully")

    async def shutdown(self):
        """Shutdown the proxy manager"""
        self.logger.info("Shutting down proxy manager...")

        # Stop health monitoring
        await self.stop_health_monitoring()

        self.logger.info("Proxy manager shutdown complete")

    async def add_proxy_pool(self, proxy_list: List[str], pool_type: str = "datacenter") -> int:
        """
        Add and validate proxy pool

        Args:
            proxy_list: List of proxy URLs/configurations
            pool_type: Type of proxy pool (residential, datacenter, mobile, free)

        Returns:
            Number of successfully validated proxies
        """
        if pool_type not in self.proxy_pools:
            raise ValueError(f"Invalid pool type: {pool_type}")

        self.logger.info(f"Adding {len(proxy_list)} proxies to {pool_type} pool")

        validated_count = 0
        for proxy_config in proxy_list:
            try:
                if await self.validate_proxy(proxy_config):
                    proxy_data = {
                        "config": proxy_config,
                        "pool_type": pool_type,
                        "added_at": datetime.now(),
                        "geographic_location": await self._detect_location(proxy_config),
                        "proxy_id": self._generate_proxy_id(proxy_config)
                    }

                    self.proxy_pools[pool_type].append(proxy_data)
                    self.proxy_metrics[proxy_data["proxy_id"]] = ProxyMetrics()
                    validated_count += 1

            except Exception as e:
                self.logger.warning(f"Failed to validate proxy {proxy_config}: {e}")

        self.logger.info(f"Successfully added {validated_count}/{len(proxy_list)} proxies to {pool_type} pool")
        return validated_count

    async def validate_proxy(self, proxy_config: str) -> bool:
        """
        Validate proxy connectivity and functionality

        Args:
            proxy_config: Proxy configuration string (e.g., "http://user:pass@host:port")

        Returns:
            True if proxy is valid and functional
        """
        try:
            # Parse proxy configuration
            parsed = self._parse_proxy_config(proxy_config)
            if not parsed:
                return False

            # Test connectivity with multiple test URLs
            test_urls = [
                "http://httpbin.org/ip",
                "https://api.ipify.org?format=json",
                "http://icanhazip.com"
            ]

            for test_url in test_urls:
                try:
                    start_time = time.time()

                    connector = aiohttp.TCPConnector(limit=1)
                    timeout = aiohttp.ClientTimeout(total=self.validation_timeout)

                    async with aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout
                    ) as session:
                        async with session.get(
                            test_url,
                            proxy=proxy_config,
                            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                        ) as response:
                            if response.status == 200:
                                response_time = time.time() - start_time
                                self.logger.debug(f"Proxy {proxy_config} validated successfully (response time: {response_time:.2f}s)")
                                return True

                except Exception as e:
                    self.logger.debug(f"Proxy validation failed for {test_url}: {e}")
                    continue

            return False

        except Exception as e:
            self.logger.warning(f"Proxy validation error for {proxy_config}: {e}")
            return False

    async def get_optimal_proxy(
        self,
        target_url: Optional[str] = None,
        strategy: str = "failure_aware",
        requirements: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Select optimal proxy based on strategy and requirements

        Args:
            target_url: Target URL for geographic optimization
            strategy: Rotation strategy to use
            requirements: Additional requirements (geography, speed, etc.)

        Returns:
            Selected proxy configuration or None if no suitable proxy found
        """
        try:
            # Get available proxies based on requirements
            available_proxies = self._filter_proxies(requirements)

            if not available_proxies:
                self.logger.warning("No available proxies found")
                return None

            # Apply rotation strategy
            if strategy not in self.rotation_strategies:
                self.logger.warning(f"Unknown strategy {strategy}, using failure_aware")
                strategy = "failure_aware"

            selected_proxy = await self.rotation_strategies[strategy](available_proxies, target_url)

            if selected_proxy:
                # Update usage statistics
                self._update_proxy_usage(selected_proxy)
                self.logger.debug(f"Selected proxy: {selected_proxy['proxy_id']} using {strategy} strategy")

            return selected_proxy

        except Exception as e:
            self.logger.error(f"Error selecting optimal proxy: {e}")
            return None

    def _filter_proxies(self, requirements: Optional[Dict] = None) -> List[Dict]:
        """
        Filter proxies based on requirements

        Args:
            requirements: Dictionary with filtering criteria

        Returns:
            List of proxies matching requirements
        """
        all_proxies = []
        for pool_type, proxies in self.proxy_pools.items():
            all_proxies.extend(proxies)

        if not requirements:
            # Filter out unhealthy proxies
            return [p for p in all_proxies if self._is_proxy_healthy(p)]

        filtered_proxies = []
        for proxy in all_proxies:
            # Check health first
            if not self._is_proxy_healthy(proxy):
                continue

            # Apply filters
            if "pool_type" in requirements:
                if proxy["pool_type"] not in requirements["pool_type"]:
                    continue

            if "geographic_location" in requirements:
                required_locations = requirements["geographic_location"]
                if proxy.get("geographic_location") not in required_locations:
                    continue

            if "min_success_rate" in requirements:
                metrics = self.proxy_metrics.get(proxy["proxy_id"])
                if metrics and metrics.success_rate < requirements["min_success_rate"]:
                    continue

            if "max_response_time" in requirements:
                metrics = self.proxy_metrics.get(proxy["proxy_id"])
                if metrics and metrics.average_response_time > requirements["max_response_time"]:
                    continue

            filtered_proxies.append(proxy)

        return filtered_proxies

    def _is_proxy_healthy(self, proxy: Dict) -> bool:
        """Check if proxy is healthy based on metrics"""
        metrics = self.proxy_metrics.get(proxy["proxy_id"])
        if not metrics:
            return True  # New proxy, assume healthy

        return (
            metrics.health_score >= self.min_health_score and
            metrics.consecutive_failures < self.max_consecutive_failures
        )

    def _update_proxy_usage(self, proxy: Dict):
        """Update proxy usage statistics"""
        proxy["last_used"] = datetime.now()
        # Additional usage tracking can be added here

    def _generate_proxy_id(self, proxy_config: str) -> str:
        """Generate unique ID for proxy"""
        import hashlib
        return hashlib.md5(proxy_config.encode()).hexdigest()[:12]

    def _parse_proxy_config(self, proxy_config: str) -> Optional[Dict]:
        """Parse proxy configuration string"""
        try:
            if "://" not in proxy_config:
                return None

            parsed = urlparse(proxy_config)
            return {
                "scheme": parsed.scheme,
                "hostname": parsed.hostname,
                "port": parsed.port,
                "username": parsed.username,
                "password": parsed.password
            }
        except Exception:
            return None

    # Rotation Strategies

    async def _round_robin_rotation(self, proxies: List[Dict], target_url: Optional[str] = None) -> Optional[Dict]:
        """Round-robin proxy selection"""
        if not proxies:
            return None

        # Use a simple round-robin across all available proxies
        proxy = proxies[self.rotation_indices["round_robin"] % len(proxies)]
        self.rotation_indices["round_robin"] = (self.rotation_indices["round_robin"] + 1) % len(proxies)

        return proxy

    async def _least_used_rotation(self, proxies: List[Dict], target_url: Optional[str] = None) -> Optional[Dict]:
        """Select least recently used proxy"""
        if not proxies:
            return None

        # Sort by last used time (None values first)
        sorted_proxies = sorted(
            proxies,
            key=lambda p: p.get("last_used") or datetime.min
        )

        return sorted_proxies[0]

    async def _failure_aware_rotation(self, proxies: List[Dict], target_url: Optional[str] = None) -> Optional[Dict]:
        """Select proxy based on success rate and response time"""
        if not proxies:
            return None

        # Score proxies based on health metrics
        scored_proxies = []
        for proxy in proxies:
            metrics = self.proxy_metrics.get(proxy["proxy_id"])
            if not metrics:
                # New proxy gets high score
                score = 1.0
            else:
                score = metrics.health_score

            scored_proxies.append((score, proxy))

        # Select from top performers with some randomization
        scored_proxies.sort(reverse=True, key=lambda x: x[0])

        # Take top 30% or at least 1
        top_count = max(1, len(scored_proxies) // 3)
        top_proxies = scored_proxies[:top_count]

        # Weighted random selection from top proxies
        weights = [score for score, _ in top_proxies]
        selected = random.choices(top_proxies, weights=weights, k=1)[0]

        return selected[1]

    async def _geographic_rotation(self, proxies: List[Dict], target_url: Optional[str] = None) -> Optional[Dict]:
        """Select proxy based on geographic proximity to target"""
        if not proxies:
            return None

        if not target_url:
            # Fallback to failure-aware if no target URL
            return await self._failure_aware_rotation(proxies, target_url)

        # Try to determine target location
        target_location = await self._detect_target_location(target_url)

        if target_location:
            # Prefer proxies from same region
            same_region_proxies = [
                p for p in proxies
                if p.get("geographic_location", {}).get("country") == target_location.get("country")
            ]

            if same_region_proxies:
                return await self._failure_aware_rotation(same_region_proxies, target_url)

        # Fallback to failure-aware selection
        return await self._failure_aware_rotation(proxies, target_url)

    async def _random_rotation(self, proxies: List[Dict], target_url: Optional[str] = None) -> Optional[Dict]:
        """Random proxy selection"""
        if not proxies:
            return None

        return random.choice(proxies)

    async def _fastest_rotation(self, proxies: List[Dict], target_url: Optional[str] = None) -> Optional[Dict]:
        """Select fastest proxy based on response times"""
        if not proxies:
            return None

        # Sort by average response time
        sorted_proxies = []
        for proxy in proxies:
            metrics = self.proxy_metrics.get(proxy["proxy_id"])
            avg_time = metrics.average_response_time if metrics else 0.0
            sorted_proxies.append((avg_time, proxy))

        # Sort by response time (ascending)
        sorted_proxies.sort(key=lambda x: x[0])

        # Select from fastest 30%
        top_count = max(1, len(sorted_proxies) // 3)
        fastest_proxies = sorted_proxies[:top_count]

        # Random selection from fastest proxies
        return random.choice(fastest_proxies)[1]

    # Health Monitoring

    async def start_health_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
        self.logger.info("Health monitoring started")

    async def stop_health_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False

        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Health monitoring stopped")

    async def _health_monitor_loop(self):
        """Main health monitoring loop"""
        while self.monitoring_active:
            try:
                await self._check_all_proxies_health()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _check_all_proxies_health(self):
        """Check health of all proxies"""
        self.logger.debug("Starting health check for all proxies")

        tasks = []
        for pool_type, proxies in self.proxy_pools.items():
            for proxy in proxies:
                task = asyncio.create_task(self._check_proxy_health(proxy))
                tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            failed_proxies = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Health check failed: {result}")
                elif not result:
                    # Proxy failed health check
                    proxy_index = i
                    # Find the proxy that failed (this is simplified)
                    for pool_type, proxies in self.proxy_pools.items():
                        if proxy_index < len(proxies):
                            failed_proxies.append((pool_type, proxies[proxy_index]))
                            break
                        proxy_index -= len(proxies)

            # Remove consistently failing proxies
            for pool_type, proxy in failed_proxies:
                await self._handle_failed_proxy(proxy, pool_type)

        self.logger.debug("Health check completed")

    async def _check_proxy_health(self, proxy: Dict) -> bool:
        """Check individual proxy health"""
        try:
            proxy_config = proxy["config"]
            proxy_id = proxy["proxy_id"]

            start_time = time.time()

            # Test with a simple HTTP request
            connector = aiohttp.TCPConnector(limit=1)
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.get(
                    "http://httpbin.org/ip",
                    proxy=proxy_config,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; HealthCheck/1.0)"}
                ) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        # Record success
                        metrics = self.proxy_metrics.get(proxy_id)
                        if metrics:
                            metrics.record_success(response_time)
                        return True
                    else:
                        # Record failure
                        metrics = self.proxy_metrics.get(proxy_id)
                        if metrics:
                            metrics.record_failure()
                        return False

        except Exception as e:
            # Record failure
            metrics = self.proxy_metrics.get(proxy["proxy_id"])
            if metrics:
                metrics.record_failure()

            self.logger.debug(f"Proxy health check failed for {proxy['proxy_id']}: {e}")
            return False

    async def _handle_failed_proxy(self, proxy: Dict, pool_type: str):
        """Handle a consistently failing proxy"""
        metrics = self.proxy_metrics.get(proxy["proxy_id"])

        if metrics and metrics.health_score < self.min_health_score:
            self.logger.warning(f"Removing unhealthy proxy {proxy['proxy_id']} from {pool_type} pool")

            # Remove from pool
            if proxy in self.proxy_pools[pool_type]:
                self.proxy_pools[pool_type].remove(proxy)

            # Remove metrics
            if proxy["proxy_id"] in self.proxy_metrics:
                del self.proxy_metrics[proxy["proxy_id"]]

    # Location Detection

    async def _detect_location(self, proxy_config: str) -> Optional[Dict]:
        """Detect geographic location of proxy"""
        try:
            connector = aiohttp.TCPConnector(limit=1)
            timeout = aiohttp.ClientTimeout(total=15)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                # Use ipinfo.io for location detection
                async with session.get(
                    "http://ipinfo.io/json",
                    proxy=proxy_config,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; LocationDetector/1.0)"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "ip": data.get("ip"),
                            "city": data.get("city"),
                            "region": data.get("region"),
                            "country": data.get("country"),
                            "location": data.get("loc"),
                            "timezone": data.get("timezone")
                        }

        except Exception as e:
            self.logger.debug(f"Location detection failed for proxy: {e}")

        return None

    async def _detect_target_location(self, target_url: str) -> Optional[Dict]:
        """Detect geographic location of target URL"""
        try:
            parsed = urlparse(target_url)
            hostname = parsed.hostname

            if not hostname:
                return None

            # Simple IP geolocation (in production, use a proper service)
            import socket
            ip = socket.gethostbyname(hostname)

            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://ipinfo.io/{ip}/json") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "ip": ip,
                            "city": data.get("city"),
                            "region": data.get("region"),
                            "country": data.get("country"),
                            "location": data.get("loc")
                        }

        except Exception as e:
            self.logger.debug(f"Target location detection failed: {e}")

        return None

    # Statistics and Management

    def get_proxy_statistics(self) -> Dict:
        """Get comprehensive proxy statistics"""
        stats = {
            "pools": {},
            "total_proxies": 0,
            "healthy_proxies": 0,
            "unhealthy_proxies": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "overall_success_rate": 0.0
        }

        all_response_times = []

        for pool_type, proxies in self.proxy_pools.items():
            pool_stats = {
                "count": len(proxies),
                "healthy": 0,
                "unhealthy": 0,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time": 0.0,
                "success_rate": 0.0
            }

            pool_response_times = []

            for proxy in proxies:
                metrics = self.proxy_metrics.get(proxy["proxy_id"])
                if metrics:
                    if self._is_proxy_healthy(proxy):
                        pool_stats["healthy"] += 1
                    else:
                        pool_stats["unhealthy"] += 1

                    pool_stats["total_requests"] += metrics.total_requests
                    pool_stats["successful_requests"] += metrics.successful_requests
                    pool_stats["failed_requests"] += metrics.failed_requests

                    if metrics.response_times:
                        pool_response_times.extend(metrics.response_times)
                        all_response_times.extend(metrics.response_times)
                else:
                    pool_stats["healthy"] += 1  # New proxy assumed healthy

            if pool_stats["total_requests"] > 0:
                pool_stats["success_rate"] = pool_stats["successful_requests"] / pool_stats["total_requests"]

            if pool_response_times:
                pool_stats["average_response_time"] = statistics.mean(pool_response_times)

            stats["pools"][pool_type] = pool_stats
            stats["total_proxies"] += pool_stats["count"]
            stats["healthy_proxies"] += pool_stats["healthy"]
            stats["unhealthy_proxies"] += pool_stats["unhealthy"]
            stats["total_requests"] += pool_stats["total_requests"]
            stats["successful_requests"] += pool_stats["successful_requests"]
            stats["failed_requests"] += pool_stats["failed_requests"]

        if stats["total_requests"] > 0:
            stats["overall_success_rate"] = stats["successful_requests"] / stats["total_requests"]

        if all_response_times:
            stats["average_response_time"] = statistics.mean(all_response_times)

        return stats

    def get_proxy_details(self, proxy_id: Optional[str] = None) -> Dict:
        """Get detailed information about specific proxy or all proxies"""
        if proxy_id:
            # Get specific proxy details
            for pool_type, proxies in self.proxy_pools.items():
                for proxy in proxies:
                    if proxy["proxy_id"] == proxy_id:
                        metrics = self.proxy_metrics.get(proxy_id)
                        return {
                            "proxy_id": proxy_id,
                            "config": proxy["config"],
                            "pool_type": pool_type,
                            "added_at": proxy["added_at"].isoformat(),
                            "last_used": proxy.get("last_used").isoformat() if proxy.get("last_used") else None,
                            "geographic_location": proxy.get("geographic_location"),
                            "metrics": {
                                "total_requests": metrics.total_requests if metrics else 0,
                                "successful_requests": metrics.successful_requests if metrics else 0,
                                "failed_requests": metrics.failed_requests if metrics else 0,
                                "success_rate": metrics.success_rate if metrics else 1.0,
                                "average_response_time": metrics.average_response_time if metrics else 0.0,
                                "health_score": metrics.health_score if metrics else 1.0,
                                "consecutive_failures": metrics.consecutive_failures if metrics else 0,
                                "last_success": metrics.last_success.isoformat() if metrics and metrics.last_success else None,
                                "last_failure": metrics.last_failure.isoformat() if metrics and metrics.last_failure else None
                            },
                            "is_healthy": self._is_proxy_healthy(proxy)
                        }
            return {"error": "Proxy not found"}
        else:
            # Get all proxy details
            all_proxies = []
            for pool_type, proxies in self.proxy_pools.items():
                for proxy in proxies:
                    proxy_details = self.get_proxy_details(proxy["proxy_id"])
                    all_proxies.append(proxy_details)
            return {"proxies": all_proxies}

    async def remove_proxy(self, proxy_id: str) -> bool:
        """Remove a specific proxy from the pool"""
        for pool_type, proxies in self.proxy_pools.items():
            for proxy in proxies:
                if proxy["proxy_id"] == proxy_id:
                    proxies.remove(proxy)
                    if proxy_id in self.proxy_metrics:
                        del self.proxy_metrics[proxy_id]
                    self.logger.info(f"Removed proxy {proxy_id} from {pool_type} pool")
                    return True
        return False

    async def clear_pool(self, pool_type: str) -> int:
        """Clear all proxies from a specific pool"""
        if pool_type not in self.proxy_pools:
            return 0

        count = len(self.proxy_pools[pool_type])

        # Remove metrics for all proxies in the pool
        for proxy in self.proxy_pools[pool_type]:
            proxy_id = proxy["proxy_id"]
            if proxy_id in self.proxy_metrics:
                del self.proxy_metrics[proxy_id]

        # Clear the pool
        self.proxy_pools[pool_type] = []

        self.logger.info(f"Cleared {count} proxies from {pool_type} pool")
        return count

    def record_proxy_result(self, proxy_id: str, success: bool, response_time: float = 0.0):
        """Record the result of using a proxy"""
        metrics = self.proxy_metrics.get(proxy_id)
        if metrics:
            if success:
                metrics.record_success(response_time)
            else:
                metrics.record_failure()

    def get_best_proxies(self, count: int = 5, pool_type: Optional[str] = None) -> List[Dict]:
        """Get the best performing proxies"""
        proxies = []

        if pool_type:
            if pool_type in self.proxy_pools:
                proxies = self.proxy_pools[pool_type]
        else:
            for pool_proxies in self.proxy_pools.values():
                proxies.extend(pool_proxies)

        # Filter healthy proxies and sort by health score
        healthy_proxies = [p for p in proxies if self._is_proxy_healthy(p)]

        scored_proxies = []
        for proxy in healthy_proxies:
            metrics = self.proxy_metrics.get(proxy["proxy_id"])
            score = metrics.health_score if metrics else 1.0
            scored_proxies.append((score, proxy))

        # Sort by score (descending) and return top N
        scored_proxies.sort(reverse=True, key=lambda x: x[0])
        return [proxy for _, proxy in scored_proxies[:count]]