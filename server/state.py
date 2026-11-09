# server/state.py
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import WebSocket
import asyncio

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
        self.simulation_active: bool = True  # Por defecto activa para dinamizar pantalla
        self.active_connections: List[WebSocket] = []
        self._counter: int = 0

    def next_node_id(self) -> str:
        self._counter += 1
        self.metrics["total_visitors"] = self._counter
        return f"#{self._counter:02d}"

    def add_device(self, fingerprint: Dict[str, Any]) -> str:
        node_id = self.next_node_id()
        fingerprint["node_id"] = node_id
        fingerprint["timestamp"] = datetime.now().strftime("%H:%M:%S")
        self.devices.append(fingerprint)
        return node_id

    def add_mitm_event(self, event_data: Dict[str, Any]):
        event_data["timestamp"] = datetime.now().strftime("%H:%M:%S")
        self.events.insert(0, event_data)
        if len(self.events) > 50:
            self.events = self.events[:50]

    def add_to_protected_wall(self, entry: Dict[str, Any]):
        entry["timestamp"] = datetime.now().strftime("%H:%M:%S")
        self.protected_wall.insert(0, entry)
        if len(self.protected_wall) > 20:
            self.protected_wall = self.protected_wall[:20]

    def reset(self):
        self.devices.clear()
        self.events.clear()
        self.protected_wall.clear()
        self.metrics = {
            "total_visitors": 0,
            "plain_captures": 0,
            "encrypted_blocks": 0
        }
        self._counter = 0
        self.simulation_active = True

    async def connect_ws(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect_ws(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for dead_conn in disconnected:
            self.disconnect_ws(dead_conn)

room_state = RoomState()
