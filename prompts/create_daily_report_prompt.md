# Prompt: Crear reporte diario automatizado ERP-EDUCATIVA

## Objetivo

Corregir la validación SHA256 del sistema de backups y crear un generador de reportes diarios de operación para ERP-EDUCATIVA.

## Cambios autorizados

1. **Corregir checksum de backups**
   - Archivo: `scripts/script_backup_postgres.sh`
   - Reemplazar la línea:
     ```bash
     sha256sum "${BACKUP_PATH}" | awk '{print $1}' > "${SHA_FILE}"
     ```
     por:
     ```bash
     sha256sum "${BACKUP_PATH}" > "${SHA_FILE}"
     ```
   - Permite validar con:
     ```bash
     sha256sum -c backups/*.sha256
     ```

2. **Crear script `scripts/generar_reporte_diario.sh`**
   - Genera automáticamente un archivo Markdown en `docs/auditorias/estado_YYYY-MM-DD.md`.
   - Incluye:
     - Fecha y hora
     - Resultado de `health_check_erp.sh`
     - Resultado de `verificar_backups.sh`
     - Resultado de `verificar_espacio.sh`
     - Salida de `docker ps`
     - Salida de `docker stats --no-stream`
     - Espacio libre del servidor (`df -h`)
     - Estado general (OPERATIVO / ADVERTENCIAS / CRÍTICO) basado en los exit codes de los checks.
   - Formato Markdown profesional.
   - El script debe ser ejecutable (`chmod +x`).

## Restricciones

- No modificar `backend/` ni `frontend/`.
- No tocar `docker-compose.dev.yml`.
- No ejecutar migraciones.
- No hacer commits ni push.
- No reiniciar contenedores.

## Validación

Ejecutar:
```bash
./scripts/generar_reporte_diario.sh
```
Verificar que exista:
```
docs/auditorias/estado_$(date +%Y-%m-%d).md
```
Mostrar la ruta y el tamaño del archivo generado.
