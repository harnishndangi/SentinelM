import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from backend.app.websocket.connection_manager import manager
from backend.app.websocket.events import EventType
from backend.app.core.logging import logger

router = APIRouter(tags=["Real-time WebSockets"])


@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket streaming endpoint.
    Broadcasts operational events:
    - MODEL_HEALTH_CHANGED
    - DRIFT_DETECTED
    - INCIDENT_CREATED
    - RETRAINING_STARTED
    - TRAINING_PROGRESS
    - CANDIDATE_CREATED
    - QUALITY_GATE_PASSED
    - QUALITY_GATE_FAILED
    - CANARY_STARTED
    - MODEL_PROMOTED
    - MODEL_ROLLED_BACK
    - INCIDENT_RESOLVED
    """
    await manager.connect(websocket)
    try:
        # Send initial handshake welcome payload
        await manager.send_personal_message(
            {
                "type": "CONNECTION_ESTABLISHED",
                "message": "Connected to SentinelML Real-Time WebSocket Event Stream",
                "supported_events": [e.value for e in EventType],
            },
            websocket,
        )

        while True:
            # Handle incoming ping / messages from frontend clients
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "PING":
                    await manager.send_personal_message({"type": "PONG"}, websocket)
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket connection exception", error=str(e))
        manager.disconnect(websocket)
