---
name: rayosx-workflow
description: >-
  Flujo de trabajo guiado para desarrollar, probar y verificar cada fase del
  proyecto rayosX ("El Rayos X del Wi-Fi Público") siguiendo PLAN.md y TASKS.md.
  Activar cuando el usuario pida avanzar con el plan, implementar una fase o
  verificar el estado del proyecto.
---

# Skill: Flujo de Desarrollo `rayosX`

## Procedimiento Paso a Paso

1. **Sincronizar con el Plan**:
   - Leer `TASKS.md` para identificar la primera tarea pendiente (`[ ]`).
   - Revisar la sección correspondiente en `PLAN.md` para asegurar que todos los detalles de arquitectura se cumplan.

2. **Implementar el Módulo o Fase**:
   - Escribir código limpio, bien comentado en español y sin dependencias externas innecesarias.
   - Verificar que todas las rutas y claves JSON coincidan entre `server/`, `web/dashboard/` y `web/portal/`.

3. **Ejecutar Validación**:
   - Si se modificó `server/` o `tests/`, ejecutar:
     ```bash
     .venv/bin/pytest -v
     ```
   - Si se modificó el frontend (`web/`), verificar que los archivos estáticos se sirvan con código `200 OK` en `/dashboard` y `/reto`.

4. **Actualizar `TASKS.md`**:
   - Marcar las tareas completadas con `[x]` en `TASKS.md` y reportar al usuario un resumen claro de lo completado y cuál es el siguiente paso del plan.
