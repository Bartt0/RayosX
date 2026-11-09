# server/main.py
import os
import socket
import asyncio
import random
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse

from server.state import room_state
from server.fingerprint import extract_device_fingerprint
from server.telemetry import get_telemetry_for_device
from server.crypto_lab import process_mitm_payload

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_best_local_ip() -> str:
    """
    Detecta de forma inteligente la IP local real (Wi-Fi o Ethernet activa con salida),
    descartando adaptadores virtuales de VMware, VirtualBox, Docker y WSL.
    """
    # 1. Resolver mediante socket UDP con ruta de salida predeterminada
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.8)
        s.connect(("8.8.8.8", 80))
        routed_ip = s.getsockname()[0]
        s.close()
        # Verificar que no sea loopback ni adaptador virtual común
        if routed_ip and not routed_ip.startswith(("127.", "192.168.56.", "192.168.88.", "192.168.232.", "172.17.")):
            return routed_ip
    except Exception:
        pass

    # 2. Enumerar IPs del hostname descartando adaptadores virtuales conocidos
    try:
        hostname = socket.gethostname()
        _, _, host_ips = socket.gethostbyname_ex(hostname)
        # Priorizar redes Wi-Fi / LAN típicas
        for ip in host_ips:
            if ip.startswith(("192.168.1.", "192.168.0.", "10.0.", "10.1.")):
                return ip
        for ip in host_ips:
            if not ip.startswith(("127.", "192.168.56.", "192.168.88.", "192.168.232.", "172.17.")):
                return ip
    except Exception:
        pass

    return "127.0.0.1"

def get_all_available_ips() -> List[str]:
    """Lista las IPs útiles ordenando primero la IP Wi-Fi primaria."""
    primary = get_best_local_ip()
    ips = [primary]
    try:
        hostname = socket.gethostname()
        _, _, host_ips = socket.gethostbyname_ex(hostname)
        for ip in host_ips:
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass
    return ips

# Bucle asíncrono para telemetría continua en pantalla
async def telemetry_background_worker():
    while True:
        try:
            await asyncio.sleep(2.8)
            if room_state.active_connections and (room_state.simulation_active or len(room_state.devices) > 0):
                if room_state.devices and random.random() > 0.35:
                    target = random.choice(room_state.devices)
                    tick = get_telemetry_for_device(
                        os_name=target.get("os", "Android"),
                        node_id=target.get("node_id", "#01"),
                        simulated=False
                    )
                else:
                    sim_id = f"#{random.randint(1, max(3, len(room_state.devices))):02d}"
                    os_choice = random.choice(["Android", "iOS", "Windows"])
                    tick = get_telemetry_for_device(os_choice, sim_id, simulated=True)
                
                await room_state.broadcast({
                    "type": "telemetry_tick",
                    "tick": tick
                })
        except asyncio.CancelledError:
            break
        except Exception:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    primary_ip = get_best_local_ip()
    port = 8000
    
    print("\n" + "=" * 68)
    print("  [+] LABORATORIO: EL RAYOS X DEL WI-FI PÚBLICO (MODO ACTIVO)")
    print("=" * 68)
    print(f"  * MONITOR SOC (Tu Laptop):     http://localhost:{port}/dashboard")
    print(f"  * O también:                   http://127.0.0.1:{port}/dashboard")
    print(f"  * PORTAL MÓVIL (Para Celulares): http://{primary_ip}:{port}/reto")
    print("=" * 68)
    print("  [TIP] Conecta tu celular a la misma red Wi-Fi y escanea el QR.")
    print("=" * 68 + "\n")

    bg_task = asyncio.create_task(telemetry_background_worker())
    yield
    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Rayos X del Wi-Fi Público", lifespan=lifespan)

# Asegurar existencia de carpetas estáticas y montarlas
os.makedirs(os.path.join(BASE_DIR, "web", "dashboard"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "web", "portal"), exist_ok=True)

app.mount("/dashboard_static", StaticFiles(directory=os.path.join(BASE_DIR, "web/dashboard")), name="dashboard_static")
app.mount("/portal_static", StaticFiles(directory=os.path.join(BASE_DIR, "web/portal")), name="portal_static")

# Rutas Principales
@app.get("/")
async def serve_root():
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard")
@app.get("/dashboard/")
async def serve_dashboard():
    dashboard_file = os.path.join(BASE_DIR, "web/dashboard/index.html")
    if os.path.exists(dashboard_file):
        return FileResponse(dashboard_file)
    return HTMLResponse("<h2>Cargando Monitor SOC...</h2>", status_code=200)

@app.get("/reto")
@app.get("/reto/")
async def serve_portal():
    portal_file = os.path.join(BASE_DIR, "web/portal/index.html")
    if os.path.exists(portal_file):
        return FileResponse(portal_file)
    return HTMLResponse("<h2>Cargando Portal de Visitante...</h2>", status_code=200)

# Endpoints de API
@app.get("/api/network-info")
async def network_info(request: Request):
    best_ip = get_best_local_ip()
    all_ips = get_all_available_ips()
    return {
        "server_ip": best_ip,
        "available_ips": all_ips,
        "port": 8000,
        "portal_url": f"http://{best_ip}:8000/reto"
    }

@app.post("/api/connect")
async def connect_device(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    fingerprint = extract_device_fingerprint(request.headers, client_ip, body)
    
    node_id = room_state.add_device(fingerprint)
    
    await room_state.broadcast({
        "type": "node_joined",
        "node_id": node_id,
        "fingerprint": fingerprint,
        "metrics": room_state.metrics
    })
    
    return {
        "status": "connected",
        "node_id": node_id,
        "ip_masked": fingerprint["ip_anonima"],
        "fingerprint": fingerprint,
        "metrics": room_state.metrics
    }

@app.post("/api/transmit")
@app.post("/api/mitm")
async def transmit_data(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    mode = body.get("mode", "plain")
    secret = body.get("secret") or body.get("content") or body.get("password") or "Contraseña_123"
    alias = body.get("alias") or body.get("user") or "usuario_demo"
    node_id = body.get("node_id", "#01")

    result = process_mitm_payload(mode, secret, alias)
    is_plain = (result["mode"] == "plain")

    if is_plain:
        room_state.metrics["plain_captures"] += 1
    else:
        room_state.metrics["encrypted_blocks"] += 1

    event_data = {
        "type": "mitm_event",
        "mode": result["mode"],
        "node_id": node_id,
        "alias": alias,
        "secret": result["secret"],
        "payload_preview": result["payload_preview"],
        "cipher_hex": result["cipher_hex"],
        "sha256": result["sha256"],
        "risk_level": result["risk_level"],
        "metrics": room_state.metrics
    }

    room_state.add_mitm_event(event_data)

    if not is_plain:
        wall_entry = {
            "alias": alias,
            "node_id": node_id,
            "sha256": result["sha256"][:16] + "..."
        }
        room_state.add_to_protected_wall(wall_entry)
        event_data["protected_wall"] = room_state.protected_wall

    await room_state.broadcast(event_data)

    return {
        "status": "success",
        "mode": result["mode"],
        "alias": alias,
        "secret": result["secret"],
        "payload_preview": result["payload_preview"],
        "cipher_hex": result["cipher_hex"],
        "sha256": result["sha256"],
        "risk_level": result["risk_level"],
        "metrics": room_state.metrics,
        "result": result
    }

@app.post("/api/demo/visitor")
async def demo_visitor():
    """Genera un visitante simulado para demostraciones."""
    os_choices = [
        {"os": "Android", "browser": "Chrome Móvil", "gpu": "Adreno 730"},
        {"os": "iOS", "browser": "Safari Móvil", "gpu": "Apple A16 Bionic GPU"},
        {"os": "Windows", "browser": "Edge", "gpu": "Intel Iris Xe Graphics"}
    ]
    choice = random.choice(os_choices)
    fake_fp = {
        "ip_anonima": f"192.168.1.***",
        "os": choice["os"],
        "navegador": choice["browser"],
        "resolucion": "1080x2400 (DPR 3.0)",
        "dpr": "3.0",
        "cpu_cores": 8,
        "gpu": choice["gpu"],
        "idioma": "es-MX"
    }
    node_id = room_state.add_device(fake_fp)
    
    await room_state.broadcast({
        "type": "node_joined",
        "node_id": node_id,
        "fingerprint": fake_fp,
        "metrics": room_state.metrics
    })
    return {"status": "ok", "node_id": node_id, "fingerprint": fake_fp}

@app.post("/api/demo/mitm")
async def demo_mitm(request: Request):
    """Simula una transmisión MitM."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    mode = body.get("mode") or random.choice(["plain", "encrypted"])
    alias = body.get("alias") or f"visitante_sala_{random.randint(10, 99)}"
    secret = "PasswordSecreto_2026!" if mode == "plain" else "TokenBancario_TLS"
    node_id = body.get("node_id") or (room_state.devices[-1]["node_id"] if room_state.devices else "#01")

    result = process_mitm_payload(mode, secret, alias)
    is_plain = (result["mode"] == "plain")

    if is_plain:
        room_state.metrics["plain_captures"] += 1
    else:
        room_state.metrics["encrypted_blocks"] += 1

    event_data = {
        "type": "mitm_event",
        "mode": result["mode"],
        "node_id": node_id,
        "alias": alias,
        "secret": result["secret"],
        "payload_preview": result["payload_preview"],
        "cipher_hex": result["cipher_hex"],
        "sha256": result["sha256"],
        "risk_level": result["risk_level"],
        "metrics": room_state.metrics
    }
    room_state.add_mitm_event(event_data)

    if not is_plain:
        room_state.add_to_protected_wall({
            "alias": alias,
            "node_id": node_id,
            "sha256": result["sha256"][:16] + "..."
        })
        event_data["protected_wall"] = room_state.protected_wall

    await room_state.broadcast(event_data)
    return {"status": "ok", "event": event_data}

@app.post("/api/demo/hallway")
async def toggle_hallway():
    room_state.simulation_active = not room_state.simulation_active
    await room_state.broadcast({
        "type": "simulation_state",
        "simulation_active": room_state.simulation_active
    })
    return {"simulation_active": room_state.simulation_active}

@app.post("/api/reset")
async def reset_room():
    room_state.reset()
    await room_state.broadcast({"type": "room_reset"})
    return {"status": "reset_ok"}

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await room_state.connect_ws(websocket)
    try:
        await websocket.send_json({
            "type": "initial_state",
            "devices": room_state.devices,
            "events": room_state.events,
            "protected_wall": room_state.protected_wall,
            "metrics": room_state.metrics,
            "simulation_active": room_state.simulation_active
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        room_state.disconnect_ws(websocket)
    except Exception:
        room_state.disconnect_ws(websocket)
