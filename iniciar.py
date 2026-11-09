# iniciar.py - Lanzador amigable del Laboratorio Rayos X del Wi-Fi Público
import os
import sys
import webbrowser
import threading
import time
import socket
import uvicorn

def get_wifi_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.8)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith(("127.", "192.168.56.", "192.168.88.", "192.168.232.", "172.17.")):
            return ip
    except Exception:
        pass
    try:
        hostname = socket.gethostname()
        _, _, ips = socket.gethostbyname_ex(hostname)
        for ip in ips:
            if ip.startswith(("192.168.1.", "192.168.0.", "10.0.")):
                return ip
        for ip in ips:
            if not ip.startswith(("127.", "192.168.56.", "192.168.88.", "192.168.232.")):
                return ip
    except Exception:
        pass
    return "127.0.0.1"

def open_browser():
    time.sleep(1.2)
    url = "http://localhost:8000/dashboard"
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    wifi_ip = get_wifi_ip()
    port = 8000

    print("\n" + "=" * 70)
    print("      🚀 INICIANDO EL RAYOS X DEL WI-FI PÚBLICO (LABORATORIO SOC)")
    print("=" * 70)
    print(f"  [1] MONITOR PRINCIPAL EN TU LAPTOP:   http://localhost:{port}/dashboard")
    print(f"  [2] EN TU TELÉFONO CELULAR:          http://{wifi_ip}:{port}/reto")
    print("=" * 70)
    print("  * Abriendo automáticamente el Monitor en tu navegador...")
    print("  * Si Windows te muestra una alerta del Firewall, haz clic en:")
    print("    'Permitir acceso' para que tu teléfono pueda conectarse.")
    print("=" * 70 + "\n")

    # Abrir navegador automáticamente
    threading.Thread(target=open_browser, daemon=True).start()

    # Iniciar servidor
    uvicorn.run("server.main:app", host="0.0.0.0", port=port, reload=False)

