# server/fingerprint.py
from typing import Dict, Any

def anonymize_ip(ip: str) -> str:
    """Anonimiza el último octeto de la IP (ej. 192.168.1.45 -> 192.168.1.***)"""
    if not ip:
        return "127.0.0.1"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
    return "IPv6.Anónima.***"

def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """Extrae de forma sencilla el sistema operativo y navegador desde el User-Agent"""
    ua = user_agent.lower()
    
    # Detección de Sistema Operativo
    if "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua or "ios" in ua:
        os_name = "iOS"
    elif "windows" in ua:
        os_name = "Windows"
    elif "mac os" in ua or "macintosh" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"
    else:
        os_name = "Dispositivo Móvil"

    # Detección de Navegador
    if "chrome" in ua and "edge" not in ua:
        browser = "Chrome"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "edge" in ua:
        browser = "Edge"
    else:
        browser = "Navegador Web"

    return {"os": os_name, "navegador": browser}

def extract_device_fingerprint(headers: dict, client_ip: str, client_data: dict = None) -> Dict[str, Any]:
    ua_string = headers.get("user-agent", "")
    parsed = parse_user_agent(ua_string)
    
    client_data = client_data or {}
    
    return {
        "ip_anonima": anonymize_ip(client_ip),
        "os": parsed["os"],
        "navegador": parsed["navegador"],
        "resolucion": client_data.get("resolucion", "1080x2400"),
        "dpr": client_data.get("dpr", "2.0"),
        "cpu_cores": client_data.get("cpu_cores", "4"),
        "bateria": client_data.get("bateria", "Desconocida")
    }