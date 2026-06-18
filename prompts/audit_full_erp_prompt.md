# Prompt: Full Audit of ERP-EDUCATIVA-STABLE

**Objetivo**: Auditar integralmente el proyecto `ERP-EDUCATIVA-STABLE` sin realizar modificaciones.

**Contexto**:
- Rama estable: `main`
- Rama de desarrollo: `develop`
- Rama histórica: `forensic-baseline-2026-06`
- Versión estable actual: `v0.1.0`

---
### 1. Validaciones del repositorio Git
- Verificar existencia de ramas: `main`, `develop`, `forensic-baseline-2026-06`.
- Verificar existencia de tags, especialmente `v0.1.0`.
- Revisar estado del árbol de trabajo (no hay cambios sin commit).
- Comprobar remotos configurados y sus URLs.
- Comparar `develop` vs `main` y generar resumen de commits pendientes.
- Comparar `forensic-baseline-2026-06` vs `main` y asegurar que no haya commits posteriores a su creación.

### 2. Detección de archivos sensibles
- Buscar archivos `.env` o cualquier archivo que contenga variables de entorno con credenciales.
- Detectar cualquier archivo bajo `backups/*.sql` que esté versionado.
- Detectar claves privadas (`id_rsa`, `id_ed25519` sin extensión `.pub`).
- Buscar tokens, contraseñas o secretos expuestos en el código.

### 2.1 Validación de servicios ERP
- Verificar que el backend responda correctamente (`curl -I http://localhost:8000/api/health/`).
- Verificar que el frontend responda correctamente (`curl -I http://localhost:5174`).
- Verificar conectividad Backend ↔ PostgreSQL (`docker exec erp-educativa-db-1 pg_isready -U postgres`).
- Verificar conectividad Backend ↔ Redis (`docker exec erp-educativa-redis-1 redis-cli ping`).
- Confirmar que el Cloudflare Tunnel esté conectado (consultar logs del contenedor `tunnel` por “Connection established”).
- Detectar errores HTTP 4xx/5xx recientes en logs de backend y frontend.

### 2.2 Seguridad Git
- Verificar que el repositorio remoto sea privado.
- Detectar secretos accidentalmente versionados (usar `git grep -E "(PASSWORD|SECRET|TOKEN)"`).
- Revisar archivos ignorados por `.gitignore` (mostrar su contenido).
- Confirmar que `backups/*.sql` no estén versionados.

### 3. Auditoría de Docker
- Enumerar los contenedores: `backend`, `frontend`, `db`, `redis`, `cloudflared`.
- Revisar uso de CPU, memoria y almacenamiento de cada contenedor.
- Verificar espacio libre en disco del host (`df -h`).
- Verificar uso de espacio en Docker (`docker system df`).
- Obtener los últimos 20 logs de cada servicio (`docker compose -f docker-compose.dev.yml logs <service> --tail=20`).

### 3.1 Validación de Docker Compose
- Verificar que `docker-compose.dev.yml` exista.
- Validar sintaxis con `docker compose -f docker-compose.dev.yml config`.
- Detectar variables de entorno faltantes.
- Detectar imágenes inexistentes.
- Detectar puertos en conflicto.

### 4. Verificación de backups
- Confirmar existencia del directorio `backups/`.
- Mostrar fecha del último backup (`ls -l backups/*.sql`).
- Validar integridad de los archivos SQL:
  - Para dumps SQL planos: `head -n 20 backups/*.sql` y `tail -n 20 backups/*.sql`.
  - Para dumps custom (`.dump`): `pg_restore --list archivo.dump`.

### 4.1 Auditoría PostgreSQL
- Verificar tamaño de la base de datos.
- Contar número de tablas.
- Verificar últimas migraciones aplicadas (`docker exec erp-educativa-db-1 psql -U postgres -c "SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 5;"`).
- Detectar errores recientes en logs de PostgreSQL.
- Verificar espacio disponible para crecimiento en el volumen de datos.

### 5. Generación de informe Markdown (`audit_full_erp.md`)
El informe debe incluir:
- **Resumen de riesgos detectados** (alta, media, baja).
- **Acciones recomendadas** con prioridad.
- **Detalle de diferencias** entre ramas (`develop` vs `main`, `forensic-baseline-2026-06` vs `main`).
- **Lista de archivos sensibles** encontrados.
- **Estado de contenedores Docker** (CPU, memoria, logs).
- **Estado de Docker Compose** (configuración válida, variables faltantes, conflictos).
- **Estado de backups** (último backup, integridad).
- **Estado de servicios ERP** (salud HTTP, conectividad, túnel).
- **Auditoría PostgreSQL** (tamaño, tablas, migraciones, logs).
- **Espacio en disco** del host y uso de Docker (`df -h`, `docker system df`).

**Restricciones**:
- No modificar ni crear archivos en el repositorio.
- No crear commits, ramas ni push.
- No reiniciar contenedores.
- Solo lectura y auditoría.

---
**Uso**: Copiar este prompt y ejecutarlo con Antigravity cuando se requiera una auditoría completa del proyecto.
