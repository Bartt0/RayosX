# server/state.py
from typing import Dict, List, Any
import asyncio
from fastapi import WebSocket

class RoomState:
    def __init__(self):
        self.devices: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []
        self.protected_wall: List[Dict[str, Any]] = []
        self.metrics = {
            "total_visitors": 0,
            "plain_captures": 0,
            "encrypted_blocks": 0
        }
        self.simulation_active = False
        self.active_connections: List[WebSocket] = []

    def reset(self):
        self.devices.clear()
        self.events.clear()
        self.protected_wall.clear()
        self.metrics = {"total_visitors": 0, "plain_captures": 0, "encrypted_blocks": 0}
        self.simulation_active = False

    async def connect_ws(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect_ws(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

room_state = RoomState()