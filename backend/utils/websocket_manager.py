"""
WebSocket Connection Manager
"""

import logging
import uuid
from typing import Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections
    """

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def register(self, websocket: WebSocket) -> str:
        """Register a new WebSocket connection"""
        connection_id = str(uuid.uuid4())[:8]
        self.connections[connection_id] = websocket
        logger.info(f"Registered connection: {connection_id}")
        return connection_id

    async def unregister(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            logger.info(f"Unregistered connection: {connection_id}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        for connection_id, websocket in self.connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.connections)
