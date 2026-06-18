#!/usr/bin/env bash

# verificar_backups.sh
# Verifica que exista al menos un backup reciente y que el checksum sea válido.

set -euo pipefail

BACKUP_DIR="$(pwd)/backups"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Find most recent backup file (sql) and its sha256 file
latest_sql=$(ls -1 ${BACKUP_DIR}/backup_*.sql 2>/dev/null | sort | tail -n 1 || true)
if [ -z "$latest_sql" ]; then
  echo "No backup files found in ${BACKUP_DIR}."
  exit 1
fi

sha_file="${latest_sql}.sha256"
if [ ! -f "$sha_file" ]; then
  echo "SHA256 file missing for ${latest_sql}."
  exit 1
fi

# Verify checksum
if sha256sum -c "$sha_file" > /dev/null 2>&1; then
  echo "Backup $(basename "$latest_sql") checksum OK."
  exit 0
else
  echo "Backup $(basename "$latest_sql") checksum FAILED."
  exit 2
fi
