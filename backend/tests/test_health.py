"""
StockSense — Backend test suite.

Tests for the health check endpoint.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_200():
    """The health endpoint should return HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_check_response_body():
    """The health endpoint should return the expected JSON fields."""
    response = client.get("/api/v1/health")
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "StockSense API"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
