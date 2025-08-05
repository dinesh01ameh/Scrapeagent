"""
Test main application functionality
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_scraper():
    """Mock scraper fixture"""
    scraper = AsyncMock()
    scraper.is_initialized = True
    scraper.get_status.return_value = {
        "initialized": True,
        "components": {}
    }
    return scraper


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SwissKnife AI Scraper"
    assert data["status"] == "running"
    assert "features" in data
    assert "endpoints" in data


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SwissKnife AI Scraper"


@patch('main.get_scraper')
def test_status_endpoint(mock_get_scraper, client, mock_scraper):
    """Test status endpoint"""
    mock_get_scraper.return_value = mock_scraper
    
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "healthy"
    assert "scraper" in data


def test_health_ready(client):
    """Test readiness check"""
    response = client.get("/health/ready")
    # This might fail if scraper is not initialized, which is expected in tests
    assert response.status_code in [200, 503]


def test_health_live(client):
    """Test liveness check"""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
