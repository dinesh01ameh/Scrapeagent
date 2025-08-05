"""
Tests for Advanced Proxy Rotation System
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from features.proxy_rotation import AdvancedProxyManager, ProxyMetrics
from utils.exceptions import ProxyError, ProxyValidationError


class TestProxyMetrics:
    """Test ProxyMetrics class"""
    
    def test_initial_state(self):
        """Test initial metrics state"""
        metrics = ProxyMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 1.0
        assert metrics.average_response_time == 0.0
        assert metrics.health_score == 1.0
        assert metrics.consecutive_failures == 0
    
    def test_record_success(self):
        """Test recording successful requests"""
        metrics = ProxyMetrics()
        
        metrics.record_success(0.5)
        metrics.record_success(1.0)
        
        assert metrics.total_requests == 2
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 1.0
        assert metrics.average_response_time == 0.75
        assert metrics.consecutive_failures == 0
    
    def test_record_failure(self):
        """Test recording failed requests"""
        metrics = ProxyMetrics()
        
        metrics.record_failure()
        metrics.record_failure()
        
        assert metrics.total_requests == 2
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 2
        assert metrics.success_rate == 0.0
        assert metrics.consecutive_failures == 2
    
    def test_health_score_calculation(self):
        """Test health score calculation"""
        metrics = ProxyMetrics()
        
        # All successful requests should have high health score
        for _ in range(10):
            metrics.record_success(0.5)
        
        assert metrics.health_score > 0.9
        
        # Add some failures
        for _ in range(5):
            metrics.record_failure()
        
        # Health score should decrease
        assert metrics.health_score < 0.9


class TestAdvancedProxyManager:
    """Test AdvancedProxyManager class"""
    
    @pytest.fixture
    async def proxy_manager(self):
        """Create proxy manager for testing"""
        config = {
            "health_check_interval": 60,
            "max_consecutive_failures": 3,
            "min_health_score": 0.5,
            "validation_timeout": 5
        }
        manager = AdvancedProxyManager(config)
        yield manager
        await manager.shutdown()
    
    def test_initialization(self, proxy_manager):
        """Test proxy manager initialization"""
        assert len(proxy_manager.proxy_pools) == 4
        assert "residential" in proxy_manager.proxy_pools
        assert "datacenter" in proxy_manager.proxy_pools
        assert "mobile" in proxy_manager.proxy_pools
        assert "free" in proxy_manager.proxy_pools
        assert len(proxy_manager.rotation_strategies) == 6
    
    @patch('aiohttp.ClientSession.get')
    async def test_validate_proxy_success(self, mock_get, proxy_manager):
        """Test successful proxy validation"""
        # Mock successful HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await proxy_manager.validate_proxy("http://proxy.example.com:8080")
        assert result is True
    
    @patch('aiohttp.ClientSession.get')
    async def test_validate_proxy_failure(self, mock_get, proxy_manager):
        """Test failed proxy validation"""
        # Mock failed HTTP response
        mock_get.side_effect = aiohttp.ClientError("Connection failed")
        
        result = await proxy_manager.validate_proxy("http://invalid-proxy.com:8080")
        assert result is False
    
    @patch.object(AdvancedProxyManager, 'validate_proxy')
    @patch.object(AdvancedProxyManager, '_detect_location')
    async def test_add_proxy_pool(self, mock_location, mock_validate, proxy_manager):
        """Test adding proxy pool"""
        mock_validate.return_value = True
        mock_location.return_value = {"country": "US", "city": "New York"}
        
        proxy_list = [
            "http://proxy1.example.com:8080",
            "http://proxy2.example.com:8080"
        ]
        
        count = await proxy_manager.add_proxy_pool(proxy_list, "datacenter")
        
        assert count == 2
        assert len(proxy_manager.proxy_pools["datacenter"]) == 2
        assert len(proxy_manager.proxy_metrics) == 2
    
    async def test_get_optimal_proxy_no_proxies(self, proxy_manager):
        """Test getting optimal proxy when no proxies available"""
        result = await proxy_manager.get_optimal_proxy()
        assert result is None
    
    @patch.object(AdvancedProxyManager, 'validate_proxy')
    @patch.object(AdvancedProxyManager, '_detect_location')
    async def test_rotation_strategies(self, mock_location, mock_validate, proxy_manager):
        """Test different rotation strategies"""
        mock_validate.return_value = True
        mock_location.return_value = {"country": "US"}
        
        # Add test proxies
        proxy_list = [f"http://proxy{i}.example.com:8080" for i in range(5)]
        await proxy_manager.add_proxy_pool(proxy_list, "datacenter")
        
        # Test round robin
        proxy1 = await proxy_manager.get_optimal_proxy(strategy="round_robin")
        proxy2 = await proxy_manager.get_optimal_proxy(strategy="round_robin")
        assert proxy1 != proxy2
        
        # Test random
        proxy3 = await proxy_manager.get_optimal_proxy(strategy="random")
        assert proxy3 is not None
        
        # Test failure aware
        proxy4 = await proxy_manager.get_optimal_proxy(strategy="failure_aware")
        assert proxy4 is not None
    
    def test_filter_proxies(self, proxy_manager):
        """Test proxy filtering"""
        # Add test proxy data
        test_proxy = {
            "proxy_id": "test123",
            "pool_type": "datacenter",
            "geographic_location": {"country": "US"}
        }
        proxy_manager.proxy_pools["datacenter"].append(test_proxy)
        proxy_manager.proxy_metrics["test123"] = ProxyMetrics()
        
        # Test filtering by pool type
        requirements = {"pool_type": ["datacenter"]}
        filtered = proxy_manager._filter_proxies(requirements)
        assert len(filtered) == 1
        
        # Test filtering by location
        requirements = {"geographic_location": ["US"]}
        filtered = proxy_manager._filter_proxies(requirements)
        assert len(filtered) == 1
        
        # Test filtering by non-matching criteria
        requirements = {"pool_type": ["residential"]}
        filtered = proxy_manager._filter_proxies(requirements)
        assert len(filtered) == 0
    
    def test_proxy_health_check(self, proxy_manager):
        """Test proxy health checking"""
        # Create test proxy with metrics
        test_proxy = {"proxy_id": "test123"}
        metrics = ProxyMetrics()
        
        # Healthy proxy
        for _ in range(10):
            metrics.record_success(0.5)
        proxy_manager.proxy_metrics["test123"] = metrics
        
        assert proxy_manager._is_proxy_healthy(test_proxy) is True
        
        # Unhealthy proxy
        for _ in range(10):
            metrics.record_failure()
        
        assert proxy_manager._is_proxy_healthy(test_proxy) is False
    
    def test_proxy_statistics(self, proxy_manager):
        """Test proxy statistics generation"""
        # Add test data
        test_proxy = {
            "proxy_id": "test123",
            "pool_type": "datacenter"
        }
        proxy_manager.proxy_pools["datacenter"].append(test_proxy)
        
        metrics = ProxyMetrics()
        metrics.record_success(0.5)
        metrics.record_success(1.0)
        metrics.record_failure()
        proxy_manager.proxy_metrics["test123"] = metrics
        
        stats = proxy_manager.get_proxy_statistics()
        
        assert stats["total_proxies"] == 1
        assert stats["healthy_proxies"] == 1
        assert stats["total_requests"] == 3
        assert stats["successful_requests"] == 2
        assert stats["failed_requests"] == 1
        assert stats["overall_success_rate"] == 2/3
    
    async def test_remove_proxy(self, proxy_manager):
        """Test proxy removal"""
        # Add test proxy
        test_proxy = {
            "proxy_id": "test123",
            "pool_type": "datacenter"
        }
        proxy_manager.proxy_pools["datacenter"].append(test_proxy)
        proxy_manager.proxy_metrics["test123"] = ProxyMetrics()
        
        # Remove proxy
        success = await proxy_manager.remove_proxy("test123")
        assert success is True
        assert len(proxy_manager.proxy_pools["datacenter"]) == 0
        assert "test123" not in proxy_manager.proxy_metrics
        
        # Try to remove non-existent proxy
        success = await proxy_manager.remove_proxy("nonexistent")
        assert success is False
    
    async def test_clear_pool(self, proxy_manager):
        """Test clearing proxy pool"""
        # Add test proxies
        for i in range(3):
            test_proxy = {
                "proxy_id": f"test{i}",
                "pool_type": "datacenter"
            }
            proxy_manager.proxy_pools["datacenter"].append(test_proxy)
            proxy_manager.proxy_metrics[f"test{i}"] = ProxyMetrics()
        
        # Clear pool
        count = await proxy_manager.clear_pool("datacenter")
        assert count == 3
        assert len(proxy_manager.proxy_pools["datacenter"]) == 0
        assert len([k for k in proxy_manager.proxy_metrics.keys() if k.startswith("test")]) == 0
    
    def test_get_best_proxies(self, proxy_manager):
        """Test getting best performing proxies"""
        # Add test proxies with different performance
        for i in range(5):
            test_proxy = {
                "proxy_id": f"test{i}",
                "pool_type": "datacenter"
            }
            proxy_manager.proxy_pools["datacenter"].append(test_proxy)
            
            metrics = ProxyMetrics()
            # Create different success rates
            for _ in range(10):
                if i < 3:  # First 3 proxies are better
                    metrics.record_success(0.5)
                else:
                    metrics.record_failure()
            
            proxy_manager.proxy_metrics[f"test{i}"] = metrics
        
        best_proxies = proxy_manager.get_best_proxies(count=3)
        assert len(best_proxies) == 3
        
        # Check that the best proxies are returned (test0, test1, test2)
        best_ids = [p["proxy_id"] for p in best_proxies]
        assert "test0" in best_ids
        assert "test1" in best_ids
        assert "test2" in best_ids


@pytest.mark.asyncio
class TestProxyManagerIntegration:
    """Integration tests for proxy manager"""
    
    async def test_health_monitoring_lifecycle(self):
        """Test health monitoring start/stop lifecycle"""
        manager = AdvancedProxyManager({"health_check_interval": 1})
        
        # Start monitoring
        await manager.start_health_monitoring()
        assert manager.monitoring_active is True
        assert manager.health_monitor_task is not None
        
        # Stop monitoring
        await manager.stop_health_monitoring()
        assert manager.monitoring_active is False
    
    @patch('aiohttp.ClientSession.get')
    async def test_end_to_end_proxy_usage(self, mock_get):
        """Test complete proxy usage workflow"""
        # Mock successful responses
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        manager = AdvancedProxyManager()
        
        try:
            # Add proxies
            proxy_list = ["http://proxy1.example.com:8080", "http://proxy2.example.com:8080"]
            count = await manager.add_proxy_pool(proxy_list, "datacenter")
            assert count == 2
            
            # Get optimal proxy
            proxy = await manager.get_optimal_proxy()
            assert proxy is not None
            
            # Record usage
            manager.record_proxy_result(proxy["proxy_id"], True, 0.5)
            
            # Check statistics
            stats = manager.get_proxy_statistics()
            assert stats["total_proxies"] == 2
            assert stats["successful_requests"] == 1
            
        finally:
            await manager.shutdown()
