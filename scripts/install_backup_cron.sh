#!/usr/bin/env bash

# install_backup_cron.sh
# Instala una tarea cron que ejecuta diariamente a las 02:00 AM el script de backup.
# No modifica docker‑compose ni código de la aplicación.

set -euo pipefail

# Ruta del proyecto (asume que este script está en ./scripts)
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# Ruta del script de backup y del log
BACKUP_SCRIPT="${PROJECT_ROOT}/scripts/script_backup_postgres.sh"
LOG_FILE="${PROJECT_ROOT}/backups/backup.log"

# Verificar que el script de backup exista y sea ejecutable
if [[ ! -x "$BACKUP_SCRIPT" ]]; then
  echo "[ERROR] No se encontró script ejecutable en $BACKUP_SCRIPT"
  exit 1
fi

# Definir la línea de cron (02:00 diariamente) usando el usuario actual
CRON_LINE_USER="0 2 * * * ${USER} ${BACKUP_SCRIPT} >> ${LOG_FILE} 2>&1"
CRON_LINE_NOUSER="0 2 * * * ${BACKUP_SCRIPT} >> ${LOG_FILE} 2>&1"

# Archivo de cron en /etc/cron.d (se necesita sudo). En entornos donde no haya sudo, se crea en el crontab del usuario.
if command -v sudo >/dev/null 2>&1; then
  CRON_FILE="/etc/cron.d/erp_backup"
  echo "$CRON_LINE_USER" | sudo tee "$CRON_FILE" > /dev/null
  sudo chmod 644 "$CRON_FILE"
  sudo systemctl reload cron || sudo service cron reload
  echo "Tarea cron instalada en $CRON_FILE"
else
  # Fallback: agregar al crontab del usuario actual (sin especificar USER)
  (crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT"; echo "$CRON_LINE_NOUSER") | crontab -
  echo "Tarea cron añadida al crontab del usuario $USER"
fi

exit 0
