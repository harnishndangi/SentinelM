import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.celery_app import celery_app
from backend.app.database import Base, engine


@pytest.fixture(autouse=True)
def setup_test_env():
    """Autouse fixture to set Celery to eager mode during pytest execution."""
    celery_app.conf.task_always_eager = True
    Base.metadata.create_all(bind=engine)
    yield
    celery_app.conf.task_always_eager = False


@pytest.fixture
def client():
    """Test client fixture for FastAPI app testing."""
    with TestClient(app) as test_client:
        yield test_client

