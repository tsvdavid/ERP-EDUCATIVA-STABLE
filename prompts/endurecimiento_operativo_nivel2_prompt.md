# Prompt: Endurecimiento Operativo Nivel 2 ERP-EDUCATIVA

## Objetivo

Revisar y reforzar la infraestructura de Docker para lograr un arranque inteligente y resiliente.

- Implementar dependencias con condición `service_healthy`.
- Añadir healthchecks a todos los servicios (PostgreSQL, Redis, Backend Django, Frontend React).
- Crear un sistema de métricas históricas (diario, semanal, mensual).
- Generar un reporte semanal automático.

## Alcance

- Sólo se modifican archivos en `docker-compose.dev.yml` y se añaden/actualizan documentos en `docs/` y `prompts/`.
- No se modifica código fuente (`backend/`, `frontend/`).
- No se ejecutan migraciones ni se realizan commits.

## Tareas

1. **docker-compose.dev.yml**
   - Para cada servicio, asegurarse de que `depends_on` use la forma:
     ```yaml
     depends_on:
       service_name:
         condition: service_healthy
     ```
   - Verificar que los healthchecks estén presentes y con los valores recomendados:
     - PostgreSQL: `pg_isready -U postgres`
     - Redis: `redis-cli ping`
     - Backend: `curl -f http://localhost:8000/api/health/`
     - Frontend: `curl -f http://localhost:5174`
2. **Métricas históricas**
   - Crear la estructura de directorios:
     ```
     docs/metricas/
       │
       ├── diario/
       ├── semanal/
       └── mensual/
     ```
   - Cada nivel debe registrar:
     - CPU y RAM de los contenedores (`docker stats --no-stream`).
     - Uso de disco (`df -h`).
     - Estado de los servicios (`docker ps --filter "status=healthy"`).
     - Tamaño de la base de datos (`docker exec db du -sh /var/lib/postgresql/data`).
     - Cantidad de usuarios (`psql -U postgres -c "SELECT count(*) FROM auth_user;"`).
     - Tiempo de respuesta de la API (`curl -o /dev/null -s -w "%{time_total}\n" http://localhost:8000/api/health/`).
3. **Reporte semanal automático**
   - Crear script `scripts/reporte_semanal_metricas.sh` que agregue los logs de la semana a `docs/metricas/semanal/` y genere un resumen Markdown.
   - Programar su ejecución vía cron (e.g. `0 3 * * 1`).

## Resultado esperado

- `docker compose -f docker-compose.dev.yml config` muestra dependencias con `condition: service_healthy`.
- Después de `docker compose -f docker-compose.dev.yml up -d`, `docker ps` indica:
  ```
  db        healthy
  redis     healthy
  backend   healthy
  frontend  healthy
  tunnel    Up
  ```
- Directorio `docs/metricas/` contiene subcarpetas con archivos de logs y un archivo `resumen_semanal.md`.
- Prompt disponible en `prompts/endurecimiento_operativo_nivel2_prompt.md` para ser ejecutado por Antigravity.
