import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    """Test client fixture for FastAPI app testing."""
    with TestClient(app) as test_client:
        yield test_client
