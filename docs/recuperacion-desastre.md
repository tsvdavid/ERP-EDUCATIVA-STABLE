# Recuperación ante Desastre

## Objetivo del procedimiento
Describir paso a paso cómo restaurar el ERP‑EDUCATIVA en caso de pérdida de datos o fallos críticos.

## Arquitectura ERP‑EDUCATIVA
- Backend Django
- Frontend React
- PostgreSQL
- Redis
- Docker Compose (services: backend, frontend, db, redis, cloudflared)

## Proceso de backup
1. Generar dump de PostgreSQL (`pg_dump -Fc`).
2. Guardar archivos en el directorio `backups/`.
3. Verificar SHA‑256 y tamaño.

## Proceso de restauración
1. Crear contenedor temporal `erp-recovery-db` con la misma imagen.
2. Restaurar dump en la base `erp_educativa_tmp`.
3. Levantar contenedor backend temporal conectado a la base restaurada.
4. Levantar contenedor Redis temporal.

## Validación posterior
- Verificar tabla `django_migrations` y `auth_user`.
- Ejecutar `python manage.py migrate --plan` (sin operaciones pendientes).
- Ejecutar `python manage.py check`.
- Probar caché Redis (`cache.set/get`).
- Consultar endpoint health (`curl -I http://localhost:18000/api/health/`).

## Plan de recuperación ante fallos
| Falla | Acción inmediata |
|-------|------------------|
| Pérdida total de datos | Restaurar último backup siguiendo el proceso anterior. |
| Corruptión de PostgreSQL | Ejecutar `pg_dump` de respaldo y restaurar en contenedor temporal. |
| Fallo de Redis | Levantar contenedor Redis temporal y reconfigurar backend. |
| Error humano (borrado) | Utilizar backups rotacionales (7‑4‑3) para revertir. |
