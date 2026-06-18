# Prompt: Auditoría de sincronización Git/GitHub ERP-EDUCATIVA

## Objetivo

Verificar que el workspace local de **ERP-EDUCATIVA** está completamente sincronizado con el repositorio remoto en GitHub después de crear la versión `v1.0‑operacional`.

### Restricciones (no realizar ninguna acción que modifique el repositorio)
- No hacer commits.
- No hacer push.
- No modificar archivos del proyecto.
- No ejecutar migraciones ni reiniciar Docker.
- Sólo leer información de Git.

---

## Pasos de auditoría
1. **Obtener la rama actual**
   ```bash
   git rev-parse --abbrev-ref HEAD
   ```
2. **Comprobar que el remote está configurado**
   ```bash
   git remote -v
   ```
3. **Actualizar referencias remotas sin modificar el working tree**
   ```bash
   git fetch --quiet
   ```
4. **Comparar HEAD local con el HEAD remoto**
   ```bash
   git rev-parse HEAD
   git rev-parse origin/$(git rev-parse --abbrev-ref HEAD)
   ```
   - Si los hashes coinciden → el código está sincronizado.
   - Si difieren → hay commits locales sin push o commits remotos sin pull.
5. **Verificar que la etiqueta `v1.0‑operacional` está presente tanto local como remotamente**
   ```bash
   git tag -l "v1.0-operacional"
   git ls-remote --tags origin | grep v1.0-operacional
   ```
6. **Revisar si existen archivos sin seguimiento o modificados**
   ```bash
   git status --porcelain
   ```
   - Salida vacía indica *working tree clean*.
7. **Mostrar los últimos 3 commits en ambos lados para confirmar igualdad**
   ```bash
   echo "--- Local ---"
   git log --oneline -3
   echo "--- Remote ---"
   git log --oneline -3 origin/$(git rev-parse --abbrev-ref HEAD)
   ```
8. **Resumen de auditoría**
   - Generar un reporte en `docs/auditorias/git_sync_audit_$(date +%Y-%m-%d).md` con:
     - Rama analizada.
     - Hash local vs remoto.
     - Estado de la etiqueta `v1.0‑operacional`.
     - Resultado de `git status`.
     - Observaciones de divergencias (si las hay).

---

## Resultado esperado
- `git status` muestra *nothing to commit, working tree clean*.
- Los hashes de HEAD local y remoto coinciden.
- La etiqueta `v1.0‑operacional` está disponible tanto local como en GitHub.
- No hay archivos sin seguimiento.
- El informe final indica que el workspace está completamente sincronizado.

---

## Notas operativas
- Este prompt está pensado para ser ejecutado por Antigravity o por el equipo de SRE sin crear cambios en el repositorio.
- En caso de detectar divergencias, el proceso debe detenerse y notificar al responsable antes de cualquier acción correctiva.
