# Prompt: Crear documentación oficial de Recuperación ante Desastres ERP-EDUCATIVA

## Objetivo

Crear la documentación operativa oficial de recuperación ante desastres para el proyecto ERP-EDUCATIVA.

La documentación debe explicar cómo recuperar el sistema completo después de fallos críticos como:

- pérdida del servidor.
- corrupción de la base de datos PostgreSQL.
- fallo de actualización del ERP.
- pérdida de contenedores Docker.
- necesidad de restaurar un backup validado.

La documentación debe quedar preparada para soporte técnico, auditorías internas y continuidad operativa.

---

# Contexto del proyecto

Workspace oficial:

```
/home/sistemas/.gemini/antigravity/scratch/ERP-EDUCATIVA
```

Estructura existente:

```
ERP-EDUCATIVA/
│
├── backend/ Django
├── frontend/ React
├── docker-compose.dev.yml
│
├── backups/
│   ├── backups PostgreSQL
│   └── backup.log
│
├── scripts/
│   └── script_backup_postgres.sh
│
├── docs/
│   ├── auditorias/
│   └── estructura_proyecto_ERP_EDUCATIVA.md
│
└── prompts/
```

---

# Archivo a crear

Crear:

```
docs/recuperacion-desastre.md
```

Si existe:
- conservar la estructura actual.
- mejorar contenido.
- no eliminar información útil.

---

# Contenido requerido del documento

## 1. Información general

**Título:**

```
Plan de Recuperación ante Desastres
ERP-EDUCATIVA
```

Debe incluir:
- versión del documento.
- fecha de creación.
- responsable técnico.
- objetivo del procedimiento.

## 2. Arquitectura del sistema

Documentar la arquitectura actual:

```
Usuarios
|
|
Cloudflare Tunnel
|
|
Frontend React
|
|
Backend Django
|
|
PostgreSQL
|
|
Redis Cache
```

Explicar función de cada componente.

## 3. Estructura de respaldo

Documentar:

```
ERP-EDUCATIVA

backups/
|
├── backup_YYYY_MM_DD.sql
|
├── backup_YYYY_MM_DD.sql.sha256
|
└── backup.log
```

Explicar:
- qué contiene el backup.
- cómo se genera.
- cómo verificar integridad.
- importancia del SHA256.

Relacionar con:

```
scripts/script_backup_postgres.sh
```

## 4. Procedimiento de backup manual

Incluir comando:

```bash
cd /home/sistemas/.gemini/antigravity/scratch/ERP-EDUCATIVA

./scripts/script_backup_postgres.sh
```

Validaciones:

```bash
ls -lh backups/

cat backups/backup.log

sha256sum -c backup_YYYY_MM_DD.sql.sha256
```

## 5. Escenario de recuperación completa del servidor

### Escenario

Servidor perdido completamente.

### Proceso paso a paso

1. Instalar sistema operativo.
2. Instalar Docker.
3. Recuperar código ERP (clonar/checkout del workspace oficial).
4. Configurar variables de entorno.
5. Restaurar backup PostgreSQL.
6. Levantar servicios Docker.
7. Ejecutar validaciones.

Ejemplo de levantar servicios:

```bash
docker compose -f docker-compose.dev.yml up -d
```

## 6. Restauración PostgreSQL

### Para backup SQL plano

```bash
cat backups/backup_YYYY_MM_DD.sql | docker exec -i <CONTAINER> \
    psql -U postgres -d erp_educativa
```

### Validaciones

```sql
SELECT count(*) FROM django_migrations;
SELECT count(*) FROM auth_user;
```

Explicar que se deben validar tablas críticas, migraciones y datos esenciales.

## 7. Validación Django después de restaurar

```bash
python manage.py check
python manage.py migrate --plan
```

Resultado esperado: `No planned migration operations`.

## 8. Validación Redis

```python
from django.core.cache import cache
cache.set('test','ok')
print(cache.get('test'))
```

Resultado esperado: `ok`.

## 9. Validación funcional ERP

Checklist:

| Componente | Validación |
|------------|------------|
| PostgreSQL | OK |
| Django     | OK |
| Redis      | OK |
| Frontend   | OK |
| Backend API| OK |
| Cloudflare Tunnel | OK |
| Login usuario | OK |

## 10. Recuperación después de actualización fallida

Procedimiento rollback:

1. Detectar problema.
2. Detener servicios.
3. Restaurar backup.
4. Revisar migraciones.
5. Levantar ERP.

## 11. Auditoría y evidencias

Documentar ubicación:

```
docs/auditorias/
```

Archivos:
- `audit_full_erp_YYYY-MM.md`
- `disaster_recovery_validation_YYYY-MM.md`
- `release_readiness_report.md`

Explicar que contienen evidencia técnica del proceso de auditoría y recuperación.

## 12. Política operativa

Reglas:
- Nunca modificar producción sin backup.
- Todo cambio importante debe tener rollback.
- Validar backups periódicamente.
- Mantener evidencia de pruebas de recuperación.
- No almacenar secretos en Git.

## 13. Checklist final de recuperación

| Acción | Estado |
|--------|--------|
| Backup encontrado | ☐ |
| SHA256 validado | ☐ |
| PostgreSQL restaurado | ☐ |
| Migraciones verificadas | ☐ |
| Redis validado | ☐ |
| Backend operativo | ☐ |
| Frontend operativo | ☐ |
| Health Check OK | ☐ |

## Restricciones

NO realizar:
- cambios en backend.
- cambios en frontend.
- cambios Docker.
- migraciones Django.
- commits Git.
- push remoto.
- reinicio de servicios productivos.

Solo crear documentación.

## Validación final

Después de crear el documento ejecutar:

```bash
ls -lh docs/
cat docs/recuperacion-desastre.md
```

Confirmar que el archivo fue creado correctamente, con estructura profesional y contenido orientado a soporte, sin modificaciones fuera de `docs/`.
