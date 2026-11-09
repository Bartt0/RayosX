# server/fingerprint.py
from typing import Dict, Any

def anonymize_ip(ip: str) -> str:
    """
    Anonimiza el último octeto de una dirección IP para preservar la privacidad
    Ejemplo: 192.168.1.45 -> 192.168.1.***
    """
    if not ip or ip == "testclient":
        return "192.168.1.***"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
    if ":" in ip:
        # IPv6: mostrar primeros 2 bloques
        ipv6_parts = ip.split(":")
        prefix = ":".join(ipv6_parts[:2]) if len(ipv6_parts) >= 2 else "fe80"
        return f"{prefix}::****:****"
    return "192.168.1.***"

def parse_user_agent(user_agent: str, sec_ch_ua: str = "", sec_ch_platform: str = "") -> Dict[str, str]:
    """
    Deduce el sistema operativo y navegador a partir de User-Agent y Client Hints (Sec-CH-*).
    """
    ua = (user_agent or "").lower()
    platform_hint = (sec_ch_platform or "").lower().replace('"', '')

    # 1. Sistema Operativo
    if "android" in platform_hint or "android" in ua:
        os_name = "Android"
    elif "ios" in platform_hint or any(x in ua for x in ["iphone", "ipad", "ipod"]):
        os_name = "iOS"
    elif "windows" in platform_hint or "windows nt" in ua:
        os_name = "Windows"
    elif "mac" in platform_hint or "macintosh" in ua or "mac os x" in ua:
        os_name = "macOS"
    elif "linux" in platform_hint or "linux" in ua:
        os_name = "Linux"
    elif "cros" in ua:
        os_name = "ChromeOS"
    else:
        os_name = "Móvil / Genérico"

    # 2. Navegador
    if "edg" in ua:
        browser = "Microsoft Edge"
    elif "samsungbrowser" in ua:
        browser = "Samsung Internet"
    elif "opr" in ua or "opera" in ua:
        browser = "Opera"
    elif "firefox" in ua or "fxios" in ua:
        browser = "Mozilla Firefox"
    elif "chrome" in ua or "crios" in ua:
        browser = "Google Chrome"
    elif "safari" in ua:
        browser = "Apple Safari"
    else:
        browser = "Navegador Web"

    return {"os": os_name, "navegador": browser}

def extract_device_fingerprint(headers: Any, client_ip: str, client_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Combina cabeceras HTTP del servidor con la huella digital enriquecida
    enviada por el navegador del visitante.
    """
    client_data = client_data or {}
    
    # Manejar si headers es un objeto de Starlette Headers o un diccionario común
    headers_dict = dict(headers) if headers else {}
    ua_string = headers_dict.get("user-agent", "")
    sec_ch_ua = headers_dict.get("sec-ch-ua", "")
    sec_ch_platform = headers_dict.get("sec-ch-ua-platform", "")

    parsed = parse_user_agent(ua_string, sec_ch_ua, sec_ch_platform)
    
    # Si el cliente detectó su SO por JS, usarlo preferentemente si es más específico
    client_os = client_data.get("os")
    final_os = client_os if client_os and client_os != "Desconocido" else parsed["os"]

    client_browser = client_data.get("browser")
    final_browser = client_browser if client_browser and client_browser != "Desconocido" else parsed["navegador"]

    screen_info = client_data.get("screen") or client_data.get("resolucion", "1080x2400 (DPR 2.5)")
    gpu_info = client_data.get("gpu", "Mali-G78 / Adreno 660")
    cpu_cores = client_data.get("cpu_cores", 8)
    lang = client_data.get("language") or headers_dict.get("accept-language", "es-ES").split(",")[0]

    return {
        "ip_anonima": anonymize_ip(client_ip),
        "os": final_os,
        "navegador": final_browser,
        "resolucion": screen_info,
        "dpr": client_data.get("dpr", "2.5"),
        "cpu_cores": cpu_cores,
        "gpu": gpu_info,
        "idioma": lang
    }
