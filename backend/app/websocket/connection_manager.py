import json
from typing import List, Dict, Any
from fastapi import WebSocket
from backend.app.core.logging import logger


class ConnectionManager:
    """
    Manages active WebSocket connections for real-time event broadcasting.
    Supports connection tracking, broadcasting, and personal message dispatch.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected", total_connections=len(self.active_connections))

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("Failed to send personal WebSocket message", error=str(e))

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts event payload to all active WebSocket clients."""
        if not self.active_connections:
            return

        disconnected_clients = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("Error broadcasting WebSocket event to client, marking for removal", error=str(e))
                disconnected_clients.append(connection)

        for conn in disconnected_clients:
            self.disconnect(conn)


manager = ConnectionManager()
