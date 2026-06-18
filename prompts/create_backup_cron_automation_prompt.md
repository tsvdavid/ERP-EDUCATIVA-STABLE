# Prompt: Crear automatización de backup diario con cron para ERP-EDUCATIVA

## Objetivo

Generar la documentación y los artefactos necesarios para programar la ejecución automática diaria del script de backup `script_backup_postgres.sh` mediante cron en el entorno Linux del workspace oficial.

Se deben crear dos componentes:

1. **scripts/install_backup_cron.sh** – script que instala una tarea cron que ejecuta el backup cada día a las 02:00 AM.
2. **docs/backup-operacion.md** – documento operativo que explica la configuración del cron, el flujo de respaldo y cómo validar la ejecución.

El prompt será guardado como:

```
/home/sistemas/.gemini/antigravity/scratch/ERP-EDUCATIVA/prompts/create_backup_cron_automation_prompt.md
```

Al ejecutar este prompt en Antigravity se crearán los archivos indicados manteniendo todas las restricciones vigentes (sin tocar código, Docker, migraciones, commits, etc.).

---

# Contenido del prompt

```markdown
# Prompt: Automatizar backup diario con cron para ERP-EDUCATIVA

## Objetivo

Implementar una tarea cron que ejecute automáticamente cada día a las 02:00 AM el script `scripts/script_backup_postgres.sh`.

## Paso 1 – Crear script de instalación de cron

Crear el archivo **scripts/install_backup_cron.sh** con el siguiente contenido:

```bash
#!/bin/bash

# Instalación de cron para backup diario de PostgreSQL
# ERP-EDUCATIVA

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CRON_FILE="/etc/cron.d/erp_backup"
SCRIPT_PATH="${PROJECT_DIR}/scripts/script_backup_postgres.sh"
LOG_PATH="${PROJECT_DIR}/backups/backup.log"

# Verificar que el script de backup exista y sea ejecutable
if [[ ! -x "$SCRIPT_PATH" ]]; then
  echo "[ERROR] No se encontró script ejecutable en $SCRIPT_PATH"
  exit 1
fi

# Definir la línea de cron (02:00 diariamente)
CRON_ENTRY="0 2 * * * ${USER} ${SCRIPT_PATH} >> ${LOG_PATH} 2>&1"

# Instalar la tarea (sobrescribe si ya existe)
printf "%s\n" "$CRON_ENTRY" | sudo tee "$CRON_FILE" > /dev/null

# Cambiar permisos del archivo de cron
sudo chmod 644 "$CRON_FILE"

# Recargar el demonio cron
sudo systemctl reload cron || sudo service cron reload

echo "Tarea cron instalada: $CRON_ENTRY"
```

## Paso 2 – Documentar operación de backup

Crear el archivo **docs/backup-operacion.md** con el siguiente contenido:

```markdown
# Operación de backup automático – ERP-EDUCATIVA

## 1. Visión general

- **Frecuencia**: Diario a las 02:00 AM (cron).
- **Script principal**: `scripts/script_backup_postgres.sh`.
- **Salida**: `backups/backup_YYYY_MM_DD.sql` + `backup_YYYY_MM_DD.sql.sha256`.
- **Registro**: `backups/backup.log`.

## 2. Instalación de cron

Ejecutar:

```bash
cd /home/sistemas/.gemini/antigravity/scratch/ERP-EDUCATIVA
./scripts/install_backup_cron.sh
```

Esto crea/actualiza `/etc/cron.d/erp_backup` con la línea:

```
0 2 * * * <usuario> /home/sistemas/.gemini/antigravity/scratch/ERP-EDUCATIVA/scripts/script_backup_postgres.sh >> /home/sistemas/.gemini/antigravity/scratch/ERP-EDUCATIVA/backups/backup.log 2>&1
```

## 3. Verificación de la tarea

- Listar cron del usuario: `crontab -l` o inspeccionar `/etc/cron.d/erp_backup`.
- Verificar que el archivo de log se actualiza después de la hora programada.
- Revisar la existencia de los archivos `backup_YYYY_MM_DD.sql` y su `.sha256`.

## 4. Retención y política 7‑4‑3

El script de backup ya implementa la política 7‑4‑3 (diarios, semanales, mensuales). No es necesario crear lógica adicional en cron.

## 5. Manejo de fallos

- Si el contenedor PostgreSQL está detenido, el script registra el error en `backup.log` y sale con código 1.
- En caso de espacio insuficiente en disco, el script también registra el error.
- Revisar `backup.log` para diagnosticar incidencias.

## 6. Restauración (referencia rápida)

1. Seleccionar el backup deseado:
   ```bash
   ls -lh backups/backup_YYYY_MM_DD.sql
   ```
2. Restaurar con el comando descrito en `docs/recuperacion-desastre.md`.

## 7. Auditoría

Cada ejecución genera evidencia (archivo SQL, SHA256 y log) que debe archivarse en `docs/auditorias/` mediante el proceso de validación `disaster_recovery_validation_prompt.md`.

---

## Restricciones

- No modificar código backend/frontend.
- No alterar `docker-compose.dev.yml`.
- No ejecutar migraciones.
- No crear commits ni push.
- Sólo crear archivos bajo `scripts/`, `docs/` y `prompts/`.
```

---

Al ejecutar este prompt, Antigravity debe crear los dos archivos indicados y dejar la documentación lista para su uso.
```
