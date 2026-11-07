# server/telemetry.py
import random

TELEMETRY_FEEDS = [
    {"category": "[RED SOCIAL]", "domain": "api.tiktokv.com", "desc": "Sincronización de feed en segundo plano"},
    {"category": "[RED SOCIAL]", "domain": "graph.instagram.com", "desc": "Petición de metadatos de imágenes"},
    {"category": "[RASTREADOR PUB]", "domain": "analytics.google.com", "desc": "Envío de telemetría de uso y eventos"},
    {"category": "[TELEMETRÍA OS]", "domain": "telemetry.apple.com", "desc": "Reporte de diagnóstico del sistema"},
    {"category": "[MENSAJERÍA]", "domain": "edge.whatsapp.net", "desc": "Keep-alive de conexión persistente"},
    {"category": "[RASTREADOR PUB]", "domain": "ads-collector.facebook.com", "desc": "Perfilado publicitario cruzado"}
]

def get_random_telemetry():
    feed = random.choice(TELEMETRY_FEEDS)
    return feed