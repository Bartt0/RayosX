# AGENTS.md — Guía y Configuración del Agente para `rayosX`

> **Proyecto:** "El Rayos X del Wi-Fi Público: Lo que tu celular dice a tus espaldas"  
> **Documento Maestro:** [`PLAN.md`](./PLAN.md)  
> **Seguimiento de Avance:** [`TASKS.md`](./TASKS.md)

---

## 1. Contexto y Objetivo del Proyecto

Construir un laboratorio interactivo de auditoría y concienciación en vivo que simula un **Centro de Operaciones de Seguridad (SOC)** ejecutándose 100% en la laptop del expositor sobre el Wi-Fi del recinto:
- **Sin hardware adicional** y **sin permisos de `root`** (opera en capa de aplicación HTTP/WebSockets en `:8000`).
- **100% Offline-Ready**: Sin dependencias de CDNs externos (fuentes, íconos, generador QR y audio deben funcionar en una red local aislada sin salida a Internet).
- **Dos interfaces sincronizadas en tiempo real**:
  1. **Monitor SOC (`/dashboard`)**: Proyectado en pantalla gigante 1080p, estética cyberpunk/SOC de alto contraste, 3 columnas educativas, radar en vivo, código QR dinámico, efectos con Web Audio API y atajos de teclado para el expositor.
  2. **Portal Móvil del Visitante (`/reto`)**: Web app móvil instantánea (cero fricción) donde el asistente ve su nodo asignado (`Visitante #XX`), los metadatos expuestos por su dispositivo, el laboratorio MitM (Botón Rojo HTTP vs. Botón Verde TLS/AES) y 3 recomendaciones de ciberseguridad.

---

## 2. Flujo de Trabajo del Agente (Workflow)

Para mantener un flujo ordenado, trazable y sin regresiones durante el desarrollo, el agente debe seguir este ciclo en cada tarea:

1. **Consultar Estado (`TASKS.md` y `PLAN.md`)**:
   - Antes de escribir código, revisar qué fase y tarea toca en [`TASKS.md`](./TASKS.md) y validar los requerimientos técnicos en [`PLAN.md`](./PLAN.md).
2. **Desarrollo Modular por Fases**:
   - **Fase 1:** Entorno base y Backend (`server/state.py`, `server/fingerprint.py`, `server/telemetry.py`, `server/crypto_lab.py`, `server/main.py`).
   - **Fase 2:** Portal Móvil del Visitante (`web/portal/index.html`, `styles.css`, `app.js`).
   - **Fase 3:** Monitor Gigante SOC (`web/dashboard/index.html`, `styles.css`, `audio.js`, `qrcode.min.js`, `app.js`).
   - **Fase 4:** Pruebas automatizadas (`tests/test_server.py`), script de arranque (`run.sh`) y documentación (`README.md`).
3. **Verificación Continua**:
   - Todo cambio en `server/` debe ser validado con `pytest` o pruebas de endpoints antes de dar por terminada la tarea.
   - Todo cambio en `web/` debe respetar el contrato JSON de los endpoints HTTP y eventos WebSocket definidos en el backend.
4. **Actualización de Progreso**:
   - Al completar y verificar cada entregable, marcar el ítem correspondiente `[x]` en [`TASKS.md`](./TASKS.md).

---

## 3. Reglas Técnicas y Restricciones de Arquitectura

### 3.1Privacidad y Ética (Strict Privacy by Design)
- **Anonimización obligatoria de IP**: Nunca almacenar ni proyectar la IP completa real del visitante; enmascarar siempre el último octeto (ej. `192.168.1.***`) en `fingerprint.py`.
- **Estado efímero en memoria**: Todos los datos viven únicamente en RAM (`server/state.py`). No usar bases de datos en disco ni guardar logs con datos personales. El endpoint `/api/reset` debe limpiar por completo la sala.
- **Credenciales ficticias en MitM**: El portal `/reto` debe incluir botones de autocompletado rápido con datos de prueba para evitar que los visitantes escriban contraseñas reales.

### 3.2 Cero Dependencias Externas en Frontend (100% Offline)
- Prohibido usar `<script src="https://cdn...">` o `@import url('https://fonts.googleapis.com/...')` que bloqueen la carga si el Wi-Fi del recinto no tiene salida a Internet.
- El generador QR (`web/dashboard/qrcode.min.js`) y el sintetizador de sonido (`web/dashboard/audio.js` vía `AudioContext`) deben ser locales y autónomos.

### 3.3 Contrato de Eventos WebSocket (`/ws/dashboard`)
Mantener consistencia estricta en los payloads JSON emitidos hacia el Monitor SOC:
- `initial_state`: Estado completo al conectar o reconectar el dashboard (nodos activos, métricas, muro protegido, historial MitM, estado de simulación).
- `node_joined`: Nuevo visitante conectado (`node_id`, `fingerprint`, `metrics`).
- `telemetry_tick`: Evento de consulta DNS/telemetría contextual según OS o modo Simulación de Pasillo (`node_id`, `category`, `domain`, `description`, `simulated`).
- `mitm_event`: Resultado de intercepción del laboratorio (`mode`: `"plain"` | `"encrypted"`, `node_id`, `alias`, `payload_preview`, `cipher_hex`, `sha256`, `metrics`, `protected_wall`).
- `room_reset`: Limpieza total del estado de la sala.

---

## 4. Comandos Estándar del Proyecto

- **Crear / activar entorno virtual**:
  ```bash
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```
- **Ejecutar servidor en desarrollo**:
  ```bash
  uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Ejecutar suite de pruebas**:
  ```bash
  pytest -v
  ```
- **Iniciar laboratorio para evento**:
  ```bash
  ./run.sh
  ```
