# Prompt: Sincronización Git y actualización oficial del repositorio ERP-EDUCATIVA

## Objetivo

Realizar la sincronización completa del estado actual del proyecto **ERP-EDUCATIVA** con el repositorio Git oficial y GitHub, garantizando que todos los avances de documentación, endurecimiento operativo, backups, monitoreo y configuración de infraestructura queden versionados de forma profesional.

## Alcance

- Trabajar exclusivamente sobre el workspace oficial:
  
  ```
  /home/sistemas/.gemini/antigravity/scratch/ERP-EDUCATIVA
  ```
- **No** modificar código fuente (`backend/`, `frontend/`).
- **No** ejecutar migraciones Django.
- **No** cambiar la configuración funcional ni reiniciar Docker.
- Solo validar y versionar archivos bajo `docs/`, `prompts/`, `scripts/` y `docker-compose.dev.yml`.

---

## 1. Auditoría inicial Git

```bash
cd /home/sistemas/.gemini/antigravity/scratch/ERP-EDUCATIVA

git status

git branch

git remote -v

git log --oneline -10
```

**Determinar:**
- Rama actual.
- Repositorio remoto configurado.
- Último commit existente.
- Archivos modificados.
- Archivos nuevos no rastreados.
- Archivos eliminados o renombrados.

**Resumen a generar:**
```
Estado actual Git ERP-EDUCATIVA

Rama: <branch>
Remote: <remote‑url>
Último commit: <hash> <msg>

Archivos pendientes:
- <lista>
```

---

## 2. Verificación de cambios realizados

### Documentación creada

Revisar el árbol `docs/` y validar la existencia de:
- `indice‑operativo‑erp.md`
- `arquitectura‑tecnica‑erp.md`
- `control‑operativo‑erp.md`
- `centro‑operaciones.md`
- `inventario‑activos.md`
- `seguridad‑operativa.md`
- `matriz‑riesgos.md`
- `runbook‑incidentes.md`
- `control‑cambios.md`
- `versiones‑sistema.md`

### Prompts creados

Revisar `prompts/` y validar:
- `create_architecture_documentation_prompt.md`
- `auditoria_integral_prompt.md`
- `disaster_recovery_test_prompt.md`
- `create_metrics_monitoring_prompt.md`
- `endurecimiento_operativo_nivel2_prompt.md`
- **Nuevo**: `git_sync_prompt.md`

### Scripts operativos

Revisar `scripts/` y validar la presencia de todos los scripts enumerados en la solicitud.

### Infraestructura modificada

Revisar `docker-compose.dev.yml` y confirmar que incluye:
- Healthcheck PostgreSQL.
- Healthcheck Redis.
- Healthcheck Backend.
- Healthcheck Frontend.
- `depends_on` con `condition: service_healthy` para backend → db & redis y para tunnel → frontend.
- Variables seguras Cloudflare (uso de `${TUNNEL_TOKEN}`).

---

## 3. Validación antes del commit

```bash
# No modificar código ni ejecutar migraciones

git diff --stat

git diff --check   # busca errores de formato
```

Corregir cualquier problema de estilo o whitespace.

---

## 4. Revisar archivos sensibles

```bash
git status --ignored
```

Asegurarse de que **NO** aparezcan:
- `.env`
- `backend/.env`
- `TUNNEL_TOKEN`
- Cualquier credencial o secreto.
- `backups/*.sql` u otros archivos de backup.

Si se detecta algún secreto, **detener** el proceso, notificar al responsable y no proceder con el commit.

---

## 5. Preparación del commit

**Mensaje del commit:**
```
docs: complete ERP operational documentation and infrastructure hardening
```

**Descripción del commit:**
```
- Documentación técnica completa del ERP
- Manuales operativos y runbooks
- Procedimientos de backup y recuperación
- Scripts de monitoreo y dashboard operativo
- Auditorías y métricas históricas
- Healthchecks Docker para todos los servicios
- Endurecimiento operativo nivel 2 (depends_on con service_healthy)
- Documentación de seguridad y continuidad
```

---

## 6. Ejecutar commit

```bash
git add docs/ prompts/ scripts/ docker-compose.dev.yml

git commit -m "docs: complete ERP operational documentation and infrastructure hardening"
```

---

## 7. Sincronizar con GitHub

```bash
# Verificar remoto y rama actual
git remote -v

git push origin $(git rev-parse --abbrev-ref HEAD)
```

---

## 8. Validación posterior

```bash
git status   # debe indicar "nothing to commit, working tree clean"

git log --oneline -3   # mostrar los últimos 3 commits, incluido el nuevo
```

---

## 9. Generar reporte final

Crear archivo:
```
/docs/auditorias/git_sync_report_$(date +%Y-%m-%d).md
```

**Contenido sugerido:**
```
# Reporte de sincronización Git - ERP-EDUCATIVA

## Estado inicial
- Rama: <branch>
- Último commit antes de sync: <hash> <msg>

## Cambios detectados
| Categoría   | Cantidad |
|------------|----------|
| Docs       | X |
| Prompts    | X |
| Scripts    | X |
| Infraestructura | X |

## Commit generado
- Hash: <new‑hash>
- Mensaje: docs: complete ERP operational documentation and infrastructure hardening

## Estado GitHub
- Branch remoto actualizado: sí / no
- Último commit remoto: <hash> <msg>

## Observaciones
- <cualquier incidencia, revisión de secretos, conflictos, etc.>
```

---

## Restricciones estrictas

- **No** modificar código fuente (`backend/`, `frontend/`).
- **No** ejecutar migraciones ni reiniciar Docker.
- **No** crear archivos fuera de `docs/`, `prompts/`, `scripts/` (excepto el reporte en `docs/auditorias/`).
- **No** realizar cambios automáticos si aparece un conflicto Git; detener y solicitar autorización.

---

### Resultado esperado

Al finalizar, el proyecto **ERP-EDUCATIVA** deberá quedar:
- ✅ Versionado en Git.
- ✅ Sincronizado con el repositorio remoto en GitHub.
- ✅ Con toda la documentación operativa respaldada.
- ✅ Con scripts de administración registrados.
- ✅ Con historial profesional de cambios.
- ✅ Sin secretos expuestos.

---

*Este prompt está listo para ser ejecutado por Antigravity o por el propio equipo de SRE para formalizar la versión oficial del proyecto.*
