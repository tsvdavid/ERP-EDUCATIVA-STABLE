# Arquitectura Técnica Oficial ERP-EDUCATIVA

## 1. Identificación del sistema

- **Proyecto**: ERP-EDUCATIVA
- **Tipo**: Sistema ERP Web Educativo
- **Backend**: Django
- **Frontend**: React + Vite
- **Base de datos**: PostgreSQL
- **Cache**: Redis
- **Infraestructura**: Docker + Cloudflare Tunnel

## 2. Diagrama general de arquitectura

```
                         INTERNET
                             |
                             |
                    Cloudflare Tunnel
                             |
                             |
                       Frontend React
                       Puerto 5174
                             |
                             |
                       Backend Django
                       Puerto 8000
                             |
          +------------------+------------------+
          |                                      |
          v                                      v

        PostgreSQL                              Redis
        Puerto 5432                           Puerto 6379

        Datos ERP                              Cache / Sesiones
```

*El diagrama refleja los puertos y la relación de los componentes tal como aparecen en `docker‑compose.dev.yml`.*

## 3. Arquitectura Docker

| Servicio | Imagen | Puerto expuesto | Función |
|----------|--------|----------------|---------|
| **db** | `postgres:15` | `5432:5432` | Base de datos PostgreSQL |
| **redis** | `redis:7-alpine` | `6379:6379` | Cache de sesiones |
| **backend** | `./backend` (build) | `8000:8000` | API Django (ASGI) |
| **frontend** | `./frontend` (build) | `5174:5174` | UI React (Vite) |
| **tunnel** | `cloudflare/cloudflared:latest` | – | Exposición a Internet vía Cloudflare Tunnel |

## 4. Docker Compose

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: erp_educativa
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ******
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: daphne config.asgi:application -b 0.0.0.0 -p 8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    env_file:
      - ./backend/.env

  frontend:
    build: ./frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5174:5174"
    environment:
      - NODE_ENV=development
      - VITE_API_URL_PROXY=http://backend:8000
      - API_PROXY_TARGET=http://backend:8000
    command: npm run dev -- --host 0.0.0.0 --port 5174

  tunnel:
    image: cloudflare/cloudflared:latest
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=******

volumes:
  db_data:
```

**Elementos destacados**:
- **`depends_on`** asegura que `backend` arranca después de `db`.
- **`env_file`** carga variables sensibles sin exponerlas en el compose.
- **Healthchecks** no están definidas explícitamente en esta versión.
- **Política de reinicio** (`restart: unless-stopped`) solo para el túnel.

## 5. Red interna

Docker Compose crea una red predeterminada (`erp-educativa_default`). Todos los servicios se comunican a través de ella:

```
frontend  ↔  backend  ↔  db
            ↔  redis
```

- **Frontend** solo necesita acceso al **backend** (API).
- **Backend** necesita acceso a **db** y **redis**.
- **Túnel** no necesita acceso interno a la red más allá de exponer el puerto 80/443 del contenedor del túnel.

## 6. Volúmenes persistentes

| Volumen | Servicio | Propósito |
|---------|----------|-----------|
| **db_data** | PostgreSQL | Almacena datos de la base de datos de forma persistente fuera del contenedor |

**Riesgos**:
- Eliminación accidental del volumen destruiría todos los datos de producción.
- Corrupción del volumen puede requerir restauración desde los backups generados por `script_backup_postgres.sh`.

## 7. Variables de entorno

| Servicio | Variable | Uso |
|----------|----------|-----|
| **PostgreSQL** | `POSTGRES_DB` | Nombre de la base de datos |
|  | `POSTGRES_USER` | Usuario administrador |
|  | `POSTGRES_PASSWORD` | Contraseña del usuario (ocultada) |
| **Backend (Django)** | `DATABASE_URL` | Cadena de conexión a PostgreSQL (`postgresql://postgres:******@db:5432/erp_educativa`) |
|  | `REDIS_URL` | URL de conexión a Redis (`redis://redis:6379/0`) |
|  | `SECRET_KEY` | Clave secreta de Django (ocultada) |
| **Tunnel** | `TUNNEL_TOKEN` | Token de autenticación de Cloudflare (ocultado) |
| **Frontend** | `VITE_API_URL_PROXY` / `API_PROXY_TARGET` | URL del backend para desarrollo |

> **Nota**: Los valores reales de contraseñas y tokens se sustituyen por `******` para no exponer datos sensibles.

## 8. Flujo de usuario

1. **Usuario** abre el navegador y solicita `https://<dominio>`.
2. La petición atraviesa **Cloudflare Tunnel** (TLS terminada en Cloudflare).
3. Cloudflare dirige el tráfico al **frontend React** (puerto 5174).
4. El frontend llama al **backend Django** mediante API REST (`http://backend:8000`).
5. El backend interactúa con **PostgreSQL** y **Redis** según sea necesario.
6. La respuesta viaja de vuelta a través del mismo camino hasta el navegador del usuario.

## 9. Flujo de autenticación

1. El usuario envía credenciales al endpoint `/api/auth/login/` del backend.
2. Django verifica el usuario contra la tabla `auth_user` en PostgreSQL.
3. Si la autenticación es exitosa, Django crea una sesión y guarda el identificador en **Redis**.
4. El token/sesión se devuelve al frontend, que lo almacena (e.g., `localStorage`).
5. En solicitudes posteriores, el frontend envía el token y Django lo valida mediante Redis antes de procesar la petición.

## 10. Puertos utilizados

| Servicio | Puerto interno | Puerto externo |
|----------|----------------|----------------|
| **Frontend** | 5174 | 5174 |
| **Backend** | 8000 | 8000 |
| **PostgreSQL** | 5432 | 5432 |
| **Redis** | 6379 | 6379 |
| **Tunnel** | – | Gestionado por Cloudflare (no expuesto directamente) |

## 11. Seguridad

- **Túnel Cloudflare**: elimina exposición directa de los puertos al público.
- **HTTPS**: gestionado por Cloudflare para todas las conexiones externas.
- **Variables sensibles**: almacenadas en archivos `.env` y nunca están versionadas.
- **Aislamiento de contenedores**: sólo los servicios necesarios son expuestos (frontend y backend).
- **No exponer PostgreSQL** fuera de la red interna de Docker.
- **Backups**: se almacenan fuera del contenedor y se verifica su integridad mediante SHA‑256.

## 12. Puntos críticos del sistema

### Fallo PostgreSQL
- **Impacto**: el ERP no puede leer ni escribir datos.
- **Recuperación**: restaurar el último backup usando `script_backup_postgres.sh` y volver a iniciar el contenedor `db`.

### Fallo Redis
- **Impacto**: pérdida de sesiones y cache, usuarios pueden ser forzados a re‑autenticarse.
- **Recuperación**: simplemente reiniciar el contenedor `redis`; los datos son volátiles y se vuelven a poblar.

### Fallo Cloudflare Tunnel
- **Impacto**: usuarios externos pierden acceso al frontend.
- **Recuperación**: renovar o volver a generar el `TUNNEL_TOKEN` y reiniciar el contenedor `tunnel`.

### Fallo del servidor host / Docker
- **Impacto**: todo el stack se detiene.
- **Recuperación**: reinstalar Docker, clonar el workspace oficial y volver a levantar los servicios con `docker compose up -d`.

## 13. Recuperación ante desastre

Consulte el procedimiento completo en **`docs/recuperacion-desastre.md`**. Resumen rápido:
1. Verificar disponibilidad del último backup en `backups/`.
2. Restaurar la base de datos con el script de backup (`script_backup_postgres.sh`).
3. Validar migraciones y consistencia con `python manage.py check` y `python manage.py migrate --plan`.
4. Verificar caché Redis.
5. Levantar los contenedores Docker (`docker compose -f docker-compose.dev.yml up -d`).
6. Ejecutar `curl http://localhost:8000/api/health/` para confirmar la salud del API.

## 14. Mantenimiento recomendado

### Checklist diario
- ✅ Revisar `backups/backup.log`.
- ✅ Confirmar que se haya generado un backup del día.
- ✅ Verificar espacio en disco (`df -h`).

### Checklist semanal
- ✅ Inspeccionar contenedores activos (`docker ps`).
- ✅ actualizar imágenes (`docker compose pull`).
- ✅ Revisar logs de aplicación (`docker logs backend`).

### Checklist mensual
- ✅ Ejecutar auditoría completa usando `prompts/audit_full_erp_prompt.md`.
- ✅ Realizar una restauración de prueba siguiendo `docs/recuperacion-desastre.md`.
- ✅ Revisar versiones de dependencias en `requirements.txt` y `package.json`.

---

## Restricciones de operación

- **No** modificar código en `backend/` ni `frontend/`.
- **No** alterar `docker-compose.dev.yml`.
- **No** ejecutar migraciones Django.
- **No** reiniciar contenedores de producción desde aquí.
- **No** realizar `git commit` ni `git push`.
- **Solo** crear/editar archivos bajo `docs/` y `prompts/`.

---

*Documento creado automáticamente por Antigravity a partir del workspace oficial.*
