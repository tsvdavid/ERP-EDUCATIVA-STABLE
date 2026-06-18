# SEGURIDAD OPERATIVA ERP-EDUCATIVA

## 1. Protección de credenciales

- **Variables .env**: Todas las credenciales y tokens críticos se almacenan en archivos `.env` y nunca se incluyen en el repositorio.
- **Tokens Cloudflare**: `TUNNEL_TOKEN` se mantiene en el archivo raíz `.env` y se enmascara en la documentación (`******`).
- **Contraseñas PostgreSQL**: `POSTGRES_PASSWORD` definida en el `docker‑compose.dev.yml` y también referenciada desde `.env` con valor oculto.
- **Usuarios Docker**: Los contenedores usan usuarios no privilegiados siempre que la imagen lo permita; se evita `--privileged`.

## 2. Seguridad de infraestructura

- **Docker aislado**: Cada componente corre en su propio contenedor con red interna predeterminada; solo puertos necesarios están expuestos.
- **PostgreSQL no expuesto públicamente**: En producción se recomienda cambiar `ports` a `expose` y usar un proxy interno.
- **HTTPS mediante Cloudflare Tunnel**: Todo el tráfico externo se termina en Cloudflare, garantizando TLS y ocultando la IP del host.

## 3. Control de acceso

| Rol | Nivel de acceso | Comentario |
|-----|----------------|-----------|
| **Administrador** | Total | Acceso a todos los contenedores, .env y volúmenes.
| **Soporte técnico** | Parcial | Puede ver logs, ejecutar scripts de monitoreo y backup.
| **Usuarios ERP** | Ninguno (solo frontend) | Acceso a la UI vía Cloudflare; sin acceso a infraestructura.

## 4. Protección de backups

- **SHA256**: Cada backup genera un hash `*.sha256` para verificar integridad.
- **Copias externas**: Se recomienda copiar los archivos de `backups/` a un almacenamiento fuera del host (NAS, S3, etc.) al menos una vez por semana.
- **Control de permisos**: Los archivos de backup y `backup.log` se crean con permisos `600` y pertenecen al usuario del proyecto.

## 5. Gestión de incidentes

| Caso | Acción inmediata | Responsable |
|------|------------------|-------------|
| Pérdida de acceso al túnel | Reiniciar contenedor `tunnel` y regenerar `TUNNEL_TOKEN` si es necesario | Administrador |
| Fuga de credenciales | Rotar inmediatamente variables en `.env`, invalidar tokens, notificar al equipo de seguridad | Administrador |
| Corrupción BD | Restaurar el último backup válido usando `script_backup_postgres.sh`; validar migraciones con `python manage.py check` | Soporte técnico |
| Servicio Docker caído | Ejecutar `docker compose -f docker-compose.dev.yml up -d`; revisar logs de Docker para causas | Administrador |

---

*Este documento está pensado para ser actualizado periódicamente conforme evolucionen políticas y procedimientos.*
