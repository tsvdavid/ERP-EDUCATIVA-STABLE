# Runbook de Incidentes ERP-EDUCATIVA

## Propósito

Este documento describe los pasos a seguir cuando ocurre un incidente crítico en la infraestructura del ERP-EDUCATIVA. Está pensado para el equipo de soporte y administradores de sistemas.

## 1. Caída de PostgreSQL

### Síntomas
- `docker ps` no muestra el contenedor `db` o este está en estado *Exited*.
- Los endpoints del API devuelven errores 500 o 502.
- Los logs de backup fallan.

### Acción inmediata
1. **Reiniciar contenedor**:
   ```bash
   docker compose -f docker-compose.dev.yml up -d db
   ```
2. Verificar que el contenedor esté *healthy* (si se agregan healthchecks) o que el puerto 5432 esté escuchando:
   ```bash
   docker exec -it erp-educativa-db-1 pg_isready -U postgres
   ```
3. Si el contenedor sigue fallando, revisar `docker logs db` para identificar errores de arranque.

### Recuperación
- Si la base está corrupta, restaurar el último backup:
  ```bash
  ./scripts/script_backup_postgres.sh restore <backup_file>
  ```
- Ejecutar las validaciones de `docs/recuperacion-desastre.md`.

### Notificación
- Avisar al responsable de infraestructura (ver `docs/centro-operaciones.md`).
- Registrar el incidente en el historial de auditorías (`docs/auditorias/`).

---

## 2. Caída de Redis

### Síntomas
- `docker ps` no muestra el contenedor `redis` o está *Exited*.
- Fallas de autenticación o pérdida de sesiones en la UI.

### Acción inmediata
1. Reiniciar contenedor:
   ```bash
   docker compose -f docker-compose.dev.yml up -d redis
   ```
2. Verificar conectividad:
   ```bash
   docker exec -it erp-educativa-redis-1 redis-cli ping
   ```
   Debería responder `PONG`.
3. Si el contenedor sigue fallando, revisar logs `docker logs redis`.

### Recuperación
- Redis es cache volátil; basta con reiniciar.
- Si se usaba como backend de sesiones persistente, los usuarios tendrán que volver a iniciar sesión.

---

## 3. Falta de Cloudflare Tunnel

### Síntomas
- El dominio público no responde (timeout).
- `docker ps` muestra el contenedor `tunnel` detenido.

### Acción inmediata
1. Reiniciar contenedor:
   ```bash
   docker compose -f docker-compose.dev.yml up -d tunnel
   ```
2. Verificar que el proceso `cloudflared` esté activo dentro del contenedor:
   ```bash
   docker exec -it erp-educativa-tunnel-1 ps aux | grep cloudflared
   ```
3. Si el contenedor sigue fallando, revisar la variable `TUNNEL_TOKEN` en `.env` y regenerar si es necesario.

### Recuperación
- Si el túnel está rotado, generar un nuevo token en el panel de Cloudflare y actualizar `.env`.
- Reiniciar el contenedor.

---

## 4. Caída de Docker Engine / Servicios

### Síntomas
- `docker ps` devuelve error de conexión al socket.
- Ningún contenedor está activo.

### Acción inmediata
1. Verificar el estado del servicio Docker:
   ```bash
   systemctl status docker
   ```
2. Si está detenido, iniciar:
   ```bash
   sudo systemctl start docker
   ```
3. Si Docker no arranca, revisar logs del daemon:
   ```bash
   journalctl -u docker --since "1 hour ago"
   ```
4. Una vez Docker activo, volver a levantar todos los servicios:
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

### Recuperación
- En caso de corrupción del daemon, considerar reinstalar Docker siguiendo la guía oficial de Ubuntu.
- Restaurar volúmenes si se detectó pérdida de datos.

---

## Registro de incidentes

Cada incidente debe documentarse en `docs/auditorias/` con la siguiente plantilla:

```
# INCIDENTE - <Fecha>

## Tipo
- PostgreSQL / Redis / Cloudflare / Docker

## Síntomas
- <Descripción>

## Acción tomada
- <Pasos ejecutados>

## Resultado
- <Éxito / Fallo>

## Lecciones aprendidas
- <Mejoras sugeridas>
```

Mantener este registro actualizado permite auditorías y mejora continua.
