"""
Tests for the health check endpoint.
"""


def test_health_check_returns_200(client):
    """The health endpoint should return HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_check_response_body(client):
    """The health endpoint should return the expected JSON fields."""
    response = client.get("/api/v1/health")
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "StockSense API"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
