# TASKS.md — Hoja de Ruta y Control de Flujo (`rayosX`)

Este archivo registra el progreso paso a paso siguiendo [`PLAN.md`](./PLAN.md).  
El agente debe actualizar el estado de cada tarea (`[ ]` -> `[x]`) conforme se implemente y verifique.

---

## Fase 1: Entorno Base y Backend (`server/`)
- [x] **1.1 `requirements.txt` y `.gitignore`**: Definir dependencias ligeras (`fastapi`, `uvicorn[standard]`, `cryptography`, `pytest`, `httpx`) y exclusiones de git (`.venv/`, `__pycache__/`, etc.).
- [x] **1.2 `server/__init__.py` y `server/state.py`**: Implementar estado en memoria (`RoomState`), asignación secuencial de nodos (`#01`, `#02`...), métricas del Modo Presentador, historial MitM, Muro de Usuarios Protegidos y `ConnectionManager` para WebSockets.
- [x] **1.3 `server/fingerprint.py`**: Analizador de cabeceras HTTP (`User-Agent`, `Accept-Language`, `Sec-CH-UA*`) + enriquecimiento con metadatos del cliente (resolución, DPR, CPU cores, WebGL GPU, batería/red) y anonimización de IP (`x.x.x.***`).
- [x] **1.4 `server/telemetry.py`**: Motor contextual de consultas DNS/Telemetría por sistema operativo (`Android`, `iOS`, `Desktop`) con categorías (`[RED SOCIAL]`, `[RASTREADOR PUB]`, `[TELEMETRÍA OS]`, `[MENSAJERÍA]`) y generador automático para **Modo Simulación de Pasillo**.
- [x] **1.5 `server/crypto_lab.py`**: Simulador criptográfico real:
  - Modo Inseguro (Botón Rojo): Captura de payload en texto plano y cálculo de nivel de exposición.
  - Modo Blindado (Botón Verde): Cifrado real **AES-256-CBC** + hash **SHA-256** + simulación de cabecera TLS 1.3 en hexadecimal.
- [x] **1.6 `server/main.py`**: Aplicación FastAPI con:
  - Detección multi-interfaz de IPs locales (`/api/network-info`).
  - Registro y huella de visitante (`POST /api/connect`).
  - Laboratorio MitM (`POST /api/transmit` / `/api/mitm`).
  - Endpoints de control de expositor (`POST /api/demo/visitor`, `POST /api/demo/mitm`, `POST /api/demo/hallway`, `POST /api/reset`).
  - WebSocket en tiempo real (`/ws/dashboard`) + bucle de telemetría en segundo plano.
  - Montaje de archivos estáticos para `/dashboard` y `/reto`.

---

## Fase 2: Portal Interactivo del Visitante (`web/portal/`)
- [x] **2.1 `web/portal/index.html`**: Estructura mobile-first en 3 pasos claros (Tarjetas de Huella Digital, Laboratorio MitM con autocompletado ficticio + Botón Rojo/Verde, y 3 Recomendaciones de Ciberseguridad).
- [x] **2.2 `web/portal/styles.css`**: Diseño limpio estilo Linux terminal, fondo negro, acentos verde terminal y tipografía blanca de alto contraste.
- [x] **2.3 `web/portal/app.js`**: Recolección instantánea de metadatos del navegador (pantalla, DPR, WebGL, idioma, núcleos), envío a `POST /api/connect`, botones de relleno rápido de credenciales de prueba y disparo de pruebas HTTP vs. TLS/AES hacia el servidor.

---

## Fase 3: Monitor Gigante SOC (`web/dashboard/`)
- [x] **3.1 `web/dashboard/qrcode.min.js`**: Generador de códigos QR en SVG/Canvas 100% local (sin CDNs externos).
- [x] **3.2 `web/dashboard/audio.js`**: Sintetizador de efectos de sonido con **Web Audio API** (sonar al conectar nodo, alarma roja en intercepción texto plano, acorde de escudo verde en cifrado AES-256, control de Mute).
- [x] **3.3 `web/dashboard/index.html`**: Layout 1080p de 3 columnas + barra superior con métricas del evento, selector de IP/interfaz de red, QR integrado, modal de QR gigante y barra de controles del expositor.
- [x] **3.4 `web/dashboard/styles.css`**: Tema terminal Linux / SOC de alto contraste (fondo negro, acentos verde brillante y letras blancas), radar animado con barrido, cascada DNS y overlays de alerta roja / blindaje verde.
- [x] **3.5 `web/dashboard/app.js`**: Cliente WebSocket con reconexión automática, renderizado reactivo de las 3 columnas, Modo Auto-Demo y atajos de teclado (`Espacio`, `S`, `M`, `F`, `R`, `Q`).

---

## Fase 4: Pruebas, Script de Arranque y Documentación
- [ ] **4.1 `tests/test_server.py`**: Pruebas automatizadas con `pytest` para `/api/network-info`, `/api/connect` (anonimización y nodo asignado), `/api/transmit` (texto plano vs. AES-256), `/api/reset` y `/ws/dashboard`.
- [ ] **4.2 `run.sh`**: Script ejecutable de inicio rápido que verifica el entorno, muestra las URLs locales en consola y levanta el servidor en `0.0.0.0:8000`.
- [ ] **4.3 `README.md`**: Guía de uso rápido para el expositor, controles de teclado, arquitectura y solución de problemas en redes de eventos (Client Isolation / Hotspot local).
