# Prompt: Disaster Recovery Validation for ERP-EDUCATIVA-STABLE

**Objetivo**: Validar que un backup de PostgreSQL pueda restaurarse correctamente en un entorno totalmente aislado, que la base de datos resultante sea íntegra, que Django la acepte sin migraciones pendientes, que el stack completo (PostgreSQL + Django + Redis) funcione y que la aplicación responda al endpoint de salud.

**Contexto**:
- Los backups se encuentran en `backups/` dentro del proyecto.
- Cada backup puede ser un **dump SQL plano** (`*.sql`) o un **dump custom** (`*.dump`).
- La infraestructura está definida en `docker-compose.dev.yml` (contiene PostgreSQL, Redis y el backend Django).

---
### 0️⃣ Detección dinámica de servicios Docker‑Compose
```bash
# Listar todos los servicios definidos en el compose
SERVICES=$(docker compose -f docker-compose.dev.yml config --services)

echo "Servicios detectados: $SERVICES"

# Detectar el servicio de PostgreSQL (cualquier nombre que contenga 'db' o 'postgres')
for s in $SERVICES; do
  if [[ $s == *postgres* ]] || [[ $s == *db* ]]; then
    DB_SERVICE=$s
  fi
done

# Detectar el servicio del backend Django (cualquier nombre que contenga 'backend' o 'app')
for s in $SERVICES; do
  if [[ $s == *backend* ]] || [[ $s == *app* ]]; then
    BACKEND_SERVICE=$s
  fi
done

echo "DB_SERVICE=$DB_SERVICE"
echo "BACKEND_SERVICE=$BACKEND_SERVICE"
```
> **Si la detección automática falla**, asigna manualmente `DB_SERVICE` y `BACKEND_SERVICE` con los nombres exactos de tu `docker‑compose.dev.yml`.

---
### 1️⃣ Preparación del entorno temporal
1. **Obtener la imagen exacta de PostgreSQL** usada por el contenedor de producción:
```bash
DB_CONTAINER=$(docker compose -f docker-compose.dev.yml ps -q $DB_SERVICE)
DB_IMAGE=$(docker inspect $DB_CONTAINER --format='{{.Config.Image}}')
echo "Imagen de PostgreSQL detectada: $DB_IMAGE"
```
2. **Crear una red aislada** (opcional pero recomendable):
```bash
docker network create erp-recovery-net
```
3. **Levantar un contenedor PostgreSQL temporal** usando la misma imagen:
```bash
docker run -d --name erp-recovery-db \
    --network erp-recovery-net \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=erp_educativa_tmp \
    -v $(pwd)/tmp-recovery-data:/var/lib/postgresql/data \
    $DB_IMAGE
```
- Esperar a que el contenedor indique *ready*: `docker exec erp-recovery-db pg_isready -U postgres`.

---
### 2️⃣ Verificación criptográfica y de tamaño del backup
```bash
BACKUP_FILE=backups/<archivo_de_backup>

# Tamaño legible
ls -lh $BACKUP_FILE

# SHA‑256 checksum
sha256sum $BACKUP_FILE
```
Anotar **Tamaño** y **SHA256** en el informe.

---
### 3️⃣ Restauración del backup
#### 3.1 Dump SQL plano (`*.sql`)
```bash
cat $BACKUP_FILE | docker exec -i erp-recovery-db psql -U postgres -d erp_educativa_tmp
```
#### 3.2 Dump custom (`*.dump`)
```bash
# Copiar al contenedor temporal
docker cp $BACKUP_FILE erp-recovery-db:/tmp/backup.dump
# Restaurar
docker exec erp-recovery-db pg_restore -U postgres -d erp_educativa_tmp /tmp/backup.dump
```

---
### 4️⃣ Validaciones post‑restauración
#### 4.1 PostgreSQL
1. Confirmar que la restauración terminó sin errores.
2. Listado de tablas:
```bash
docker exec erp-recovery-db psql -U postgres -d erp_educativa_tmp -c "\dt" > /tmp/recovery_tables.txt
```
3. **Conteo de filas en tablas críticas** (ejemplo estático):
```bash
for t in auth_user django_migrations myapp_estudiante myapp_docente; do
  COUNT=$(docker exec erp-recovery-db psql -U postgres -d erp_educativa_tmp -t -c "SELECT COUNT(*) FROM $t;" | tr -d '[:space:]')
  echo "$t: $COUNT" >> /tmp/recovery_counts.txt
  # Reglas de observación
  if [ "$t" = "auth_user" ] && [ "$COUNT" -eq 0 ]; then echo "Observación: auth_user vacío"; fi
  if [ "$t" = "django_migrations" ] && [ "$COUNT" -eq 0 ]; then echo "Fallo crítico: migraciones ausentes"; fi
done
```
4. Comparar esquema con la base de producción:
```bash
# Esquema producción
docker exec $DB_CONTAINER pg_dump -U postgres -s erp_educativa > /tmp/prod_schema.sql
# Esquema restaurado
docker exec erp-recovery-db pg_dump -U postgres -s erp_educativa_tmp > /tmp/recovery_schema.sql
diff -u /tmp/prod_schema.sql /tmp/recovery_schema.sql > /tmp/schema_diff.txt
```
5. Validar integridad referencial (FKs, índices):
```bash
docker exec erp-recovery-db psql -U postgres -d erp_educativa_tmp -c "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE contype='f';" > /tmp/recovery_fks.txt
```

#### 4.2 Backend temporal conectado a la base restaurada
1. **Obtener la imagen del backend** (misma que usa el service):
```bash
BACKEND_IMAGE=$(docker compose -f docker-compose.dev.yml config | grep "image:" -A1 | tail -n1 | awk '{print $2}')
```
2. **Mostrar migraciones** (debe coincidir con el código):
```bash
docker run --rm \
    --network erp-recovery-net \
    -e DB_HOST=erp-recovery-db \
    -e DB_NAME=erp_educativa_tmp \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres \
    $BACKEND_IMAGE python manage.py showmigrations
```
3. **Check de Django**:
```bash
docker run --rm \
    --network erp-recovery-net \
    -e DB_HOST=erp-recovery-db \
    -e DB_NAME=erp_educativa_tmp \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres \
    $BACKEND_IMAGE python manage.py check
```
4. **Plan de migraciones** – debe devolver *No planned migration operations*:
```bash
docker run --rm \
    --network erp-recovery-net \
    -e DB_HOST=erp-recovery-db \
    -e DB_NAME=erp_educativa_tmp \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres \
    $BACKEND_IMAGE python manage.py migrate --plan
```

#### 4.3 Validación de Redis (cache de Django)
```bash
docker run --rm \
    --network erp-recovery-net \
    -e DB_HOST=erp-recovery-db \
    -e DB_NAME=erp_educativa_tmp \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres \
    $BACKEND_IMAGE python - <<'PY'
from django.core.cache import cache
cache.set('dr_test', 'ok', 60)
print('Cache result:', cache.get('dr_test'))
PY
```
Resultado esperado: `Cache result: ok`.

#### 4.4 Validación HTTP del backend restaurado
```bash
# Iniciar backend temporal en modo detached, exponiendo puerto 18000 -> 8000
docker run -d --name erp-recovery-backend \
    --network erp-recovery-net \
    -p 18000:8000 \
    -e DB_HOST=erp-recovery-db \
    -e DB_NAME=erp_educativa_tmp \
    -e DB_USER=postgres \
    -e DB_PASSWORD=postgres \
    $BACKEND_IMAGE

# Esperar a que arranque (p. ej. sleep 5)
curl -I http://localhost:18000/api/health/
```
Debe devolver `200 OK`. Después de la prueba:
```bash
docker rm -f erp-recovery-backend
```

---
### 5️⃣ Generación del informe (`disaster_recovery_validation_report.md`)
Incluir al menos:
1. **Información del backup** – Archivo, Tamaño, SHA‑256.
2. **Resultado de la restauración** (OK/FALLADO + logs).
3. **Diff de esquema**.
4. **Listado de tablas** y **conteo de filas** (incluyendo observaciones/fallos críticos).
5. **Validación de constraints (FKs)**.
6. **Resultado de `showmigrations`** (producción) y de la base restaurada.
7. **Resultado de `manage.py check`** (sobre la base restaurada).
8. **Resultado de `manage.py migrate --plan`** (debe indicar *No planned migration operations*).
9. **Resultado de la prueba de Redis** (`ok`).
10. **Resultado HTTP** (código de estado y encabezados).
11. **Conclusión** con clasificación:
    - **APROBADO** – Todo OK.
    - **APROBADO CON OBSERVACIONES** – Diferencias menores.
    - **NO APROBADO** – Fallos críticos.
    - **CRÍTICO** – Backup corrupto o imposible de restaurar.
12. **Estado resumido** (tabla):
```
| Componente            | Estado |
|-----------------------|--------|
| Restauración DB       | OK / FAIL |
| Django check          | OK / FAIL |
| Migraciones (--plan)  | OK / FAIL |
| Redis cache test      | OK / FAIL |
| HTTP health endpoint  | OK / FAIL |
```
---
### 6️⃣ Limpieza del entorno temporal
```bash
docker rm -f erp-recovery-db
docker network rm erp-recovery-net
rm -rf tmp-recovery-data
```
Asegúrate de que no queden volúmenes ni contenedores activos.

---
**Restricciones**
- No modificar el repositorio ni crear commits.
- No ejecutar `git push`.
- Sólo operaciones de lectura/escritura en el host y contenedores temporales.
- Ejecutar con un usuario que tenga permisos Docker y acceso a `backups/`.

---
**Uso**
Copia este prompt y ejecútalo con Antigravity cuando necesites validar que un backup reciente pueda restaurarse, que Django lo acepte sin migraciones pendientes, que Redis funcione y que el ERP responda al endpoint de salud. Guarda el informe generado como `docs/auditorias/disaster_recovery_validation_YYYY-MM-DD.md`.
