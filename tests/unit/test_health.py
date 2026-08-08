def test_health_endpoint(client):
    """Verify that GET /api/v1/health returns correct healthy status json."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "sentinelml-api"
    assert data["version"] == "1.0.0"


def test_health_details_endpoint(client):
    """Verify detailed health check endpoint."""
    response = client.get("/api/v1/health/details")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "dependencies" in data
    assert data["dependencies"]["database"] == "connected"
