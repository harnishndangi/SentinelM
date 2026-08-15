import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.websocket.events import (
    EventType,
    WebSocketEvent,
    ModelHealthChangedPayload,
    DriftDetectedPayload,
    RetrainingStartedPayload,
)
from backend.app.websocket.publisher import publish_websocket_event


def test_websocket_event_models():
    """Verify strongly typed Pydantic WebSocket event payload serialization."""
    payload = DriftDetectedPayload(
        model_version_id="mod-v1.0.0",
        drift_type="FEATURE_DRIFT",
        psi_score=0.35,
        threshold=0.2,
    )
    event = WebSocketEvent(
        event_type=EventType.DRIFT_DETECTED,
        payload=payload.model_dump(),
    )
    data = event.model_dump()
    assert data["event_type"] == EventType.DRIFT_DETECTED
    assert data["payload"]["model_version_id"] == "mod-v1.0.0"
    assert data["payload"]["psi_score"] == 0.35


def test_publish_websocket_event_fallback():
    """Verify publish_websocket_event executes cleanly without throwing exceptions when Redis is offline."""
    payload = ModelHealthChangedPayload(
        model_version_id="mod-v1.0.0",
        previous_status="HEALTHY",
        new_status="DEGRADED",
        health_score=0.65,
    )
    # Should not raise exception
    publish_websocket_event(EventType.MODEL_HEALTH_CHANGED, payload)


from backend.app.database import Base, engine

def test_jobs_api_endpoints():
    """Verify GET /api/v1/jobs endpoint response structure."""
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)



def test_websocket_handshake():
    """Verify /ws/events WebSocket connection handshake."""
    client = TestClient(app)
    with client.websocket_connect("/ws/events") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "CONNECTION_ESTABLISHED"
        assert "MODEL_HEALTH_CHANGED" in data["supported_events"]
        assert "DRIFT_DETECTED" in data["supported_events"]
