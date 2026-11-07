# server/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import os

from server.state import room_state
from server.fingerprint import extract_device_fingerprint
from server.telemetry import get_random_telemetry
from server.crypto_lab import process_mitm_payload

app = FastAPI(title="Rayos X del Wi-Fi Público")

# Rutas estáticas para la web (asegúrate de que existan las carpetas web/dashboard y web/portal)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file)))
app.mount("/dashboard_static", StaticFiles(directory=os.path.join(BASE_DIR, "web/dashboard")), name="dashboard_static")
app.mount("/portal_static", StaticFiles(directory=os.path.join(BASE_DIR, "web/portal")), name="portal_static")

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    return FileResponse(os.path.join(BASE_DIR, "web/dashboard/index.html"))

@app.get("/reto", response_class=HTMLResponse)
async def serve_portal():
    return FileResponse(os.path.join(BASE_DIR, "web/portal/index.html"))

@app.get("/api/network-info")
async def network_info(request: Request):
    client_ip = request.client.host
    return {"server_ip": client_ip, "port": 8000}

@app.post("/api/connect")
async def connect_device(request: Request):
    body = await request.json() if data_is_json(request) else {}
    client_ip = request.client.host
    
    room_state.metrics["total_visitors"] += 1
    node_id = f"#{room_state.metrics['total_visitors']:02d}"
    
    fingerprint = extract_device_fingerprint(request.headers, client_ip, body)
    fingerprint["node_id"] = node_id
    
    room_state.devices.append(fingerprint)
    
    # Notificar al monitor SOC vía WebSocket
    await room_state.broadcast({
        "type": "node_joined",
        "node_id": node_id,
        "fingerprint": fingerprint,
        "metrics": room_state.metrics
    })
    
    return {"status": "connected", "node_id": node_id, "fingerprint": fingerprint}

@app.post("/api/transmit")
async def transmit_data(request: Request):
    body = await request.json()
    mode = body.get("mode", "inseguro") # "inseguro" o "cifrado"
    content = body.get("content", "")
    alias = body.get("alias", "Visitante Anónimo")
    node_id = body.get("node_id", "#01")
    
    if mode == "inseguro":
        room_state.metrics["plain_captures"] += 1
    else:
        room_state.metrics["encrypted_blocks"] += 1
        
    result = process_mitm_payload(mode, content, alias)
    
    event_data = {
        "type": "mitm_event",
        "mode": result["mode"],
        "node_id": node_id,
        "alias": alias,
        "payload_preview": result["payload_preview"],
        "cipher_hex": result["cipher_hex"],
        "sha256": result["sha256"],
        "metrics": room_state.metrics
    }
    
    room_state.events.insert(0, event_data)
    
    if mode == "cifrado":
        room_state.protected_wall.insert(0, {"alias": alias, "node_id": node_id, "sha256": result["sha256"]})
        event_data["protected_wall"] = room_state.protected_wall[:10]
        
    await room_state.broadcast(event_data)
    return {"status": "success", "result": result}

@app.post("/api/reset")
async def reset_room():
    room_state.reset()
    await room_state.broadcast({"type": "room_reset"})
    return {"status": "reset_ok"}

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await room_state.connect_ws(websocket)
    try:
        # Enviar estado inicial al conectar el dashboard
        await websocket.send_json({
            "type": "initial_state",
            "devices": room_state.devices,
            "events": room_state.events,
            "protected_wall": room_state.protected_wall,
            "metrics": room_state.metrics,
            "simulation_active": room_state.simulation_active
        })
        while True:
            # Mantener conexión abierta
            await websocket.receive_text()
    except WebSocketDisconnect:
        room_state.disconnect_ws(websocket)

def data_is_json(request: Request) -> bool:
    return "application/json" in request.headers.get("content-type", "")