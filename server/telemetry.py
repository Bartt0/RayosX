# server/telemetry.py
import random
from datetime import datetime
from typing import Dict, Any, Optional

TELEMETRY_FEEDS = {
    "Android": [
        {"category": "[TELEMETRÍA OS]", "domain": "android.clients.google.com", "desc": "Check-in periódico de Google Services Framework"},
        {"category": "[TELEMETRÍA OS]", "domain": "connectivitycheck.gstatic.com", "desc": "Sondeo de conectividad y portal cautivo Wi-Fi"},
        {"category": "[RED SOCIAL]", "domain": "api.tiktokv.com", "desc": "Sincronización de feed y perfilado en segundo plano"},
        {"category": "[RED SOCIAL]", "domain": "graph.instagram.com", "desc": "Pre-carga de reels y metadatos de sesión"},
        {"category": "[RASTREADOR PUB]", "domain": "firebase-settings.crashlytics.com", "desc": "Envío de logs de eventos y telemetría de fallos"},
        {"category": "[RASTREADOR PUB]", "domain": "app-measurement.com", "desc": "Google Analytics for Mobile Apps ping"},
        {"category": "[MENSAJERÍA]", "domain": "g.whatsapp.net", "desc": "Keep-alive de socket persistente de mensajería"},
        {"category": "[MENSAJERÍA]", "domain": "gateway.discord.gg", "desc": "Heartbeat WebSocket de presencia online"},
        {"category": "[TELEMETRÍA OS]", "domain": "tracking.miui.com", "desc": "Telemetría de fabricante y optimización de batería"}
    ],
    "iOS": [
        {"category": "[TELEMETRÍA OS]", "domain": "gateway.icloud.com", "desc": "Sincronización de llavero y estado de iCloud"},
        {"category": "[TELEMETRÍA OS]", "domain": "captive.apple.com", "desc": "Verificación del portal cautivo WISPr de iOS"},
        {"category": "[TELEMETRÍA OS]", "domain": "bag.itunes.apple.com", "desc": "Comprobación de licencias y recibos de la App Store"},
        {"category": "[RASTREADOR PUB]", "domain": "api-adservices.apple.com", "desc": "Apple Search Ads token y atribución de descargas"},
        {"category": "[MENSAJERÍA]", "domain": "courier.push.apple.com", "desc": "Conexión APNs para notificaciones instantáneas"},
        {"category": "[RED SOCIAL]", "domain": "graph.facebook.com", "desc": "SDK de Meta registrando eventos de uso de apps"},
        {"category": "[RED SOCIAL]", "domain": "t.co", "desc": "Resolución de enlaces y actividad de X/Twitter"},
        {"category": "[MENSAJERÍA]", "domain": "chat.signal.org", "desc": "Validación de llaves y mensajes en cola de Signal"}
    ],
    "Desktop": [
        {"category": "[TELEMETRÍA OS]", "domain": "v10.events.data.microsoft.com", "desc": "Windows Diagnostic Data y telemetría de teleproceso"},
        {"category": "[TELEMETRÍA OS]", "domain": "ocsp.apple.com", "desc": "Validación de certificados de seguridad macOS Gatekeeper"},
        {"category": "[RASTREADOR PUB]", "domain": "edge.activity.windows.com", "desc": "Sincronización de historial y perfil publicitario"},
        {"category": "[MENSAJERÍA]", "domain": "slack.com/api/rtm.connect", "desc": "Polling de mensajería corporativa"},
        {"category": "[RED SOCIAL]", "domain": "web.telegram.org", "desc": "Sincronización de canales de mensajería cifrada"}
    ]
}

def get_telemetry_for_device(os_name: str, node_id: str, simulated: bool = False) -> Dict[str, Any]:
    """Genera un evento de telemetría o consulta DNS contextual según el sistema operativo."""
    normalized_os = "Desktop"
    if "android" in os_name.lower():
        normalized_os = "Android"
    elif "ios" in os_name.lower() or "iphone" in os_name.lower():
        normalized_os = "iOS"
        
    feed_list = TELEMETRY_FEEDS.get(normalized_os, TELEMETRY_FEEDS["Desktop"])
    item = random.choice(feed_list)
    
    return {
        "node_id": node_id,
        "os": normalized_os,
        "category": item["category"],
        "domain": item["domain"],
        "description": item["desc"],
        "simulated": simulated,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

def get_random_telemetry() -> Dict[str, Any]:
    """Fallback genérico para compatibilidad."""
    all_feeds = TELEMETRY_FEEDS["Android"] + TELEMETRY_FEEDS["iOS"] + TELEMETRY_FEEDS["Desktop"]
    item = random.choice(all_feeds)
    return {
        "node_id": f"#{random.randint(1, 10):02d}",
        "os": "Genérico",
        "category": item["category"],
        "domain": item["domain"],
        "description": item["desc"],
        "simulated": True,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
