#!/bin/bash

# Backup oficial PostgreSQL
# ERP-EDUCATIVA
# Generación automática de respaldos

set -euo pipefail

# ----------------------------
# 1. Configuración y variables
# ----------------------------
# Directorio del proyecto (asume que este script está en scripts/ dentro del proyecto)
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_FILE="${BACKUP_DIR}/backup.log"
DATE=$(date +"%Y_%m_%d")
TIME=$(date +"%H:%M:%S")
TIMESTAMP=$(date +"%Y_%m_%d_%H%M%S")
BACKUP_FILE="backup_${TIMESTAMP}.sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"
SHA_FILE="${BACKUP_PATH}.sha256"

# Asegurar que el directorio de backups exista
mkdir -p "${BACKUP_DIR}"

# Función para escribir en el log
log() {
  echo "${DATE} ${TIME} - $1" >> "${LOG_FILE}"
}

log "Backup iniciado"

# -------------------------------------------------
# 2. Detección automática del contenedor PostgreSQL
# -------------------------------------------------
# Obtener la lista de servicios definidos en docker‑compose
SERVICES=$(docker compose -f "${PROJECT_DIR}/docker-compose.dev.yml" config --services)

# Encontrar el servicio que corresponde a PostgreSQL (contiene 'db' o 'postgres')
DB_SERVICE=""
for s in $SERVICES; do
  if [[ $s == *postgres* ]] || [[ $s == *db* ]]; then
    DB_SERVICE=$s
    break
  fi
done

if [[ -z "$DB_SERVICE" ]]; then
  log "Error: No se encontró servicio PostgreSQL en docker‑compose"
  echo "[ERROR] Servicio PostgreSQL no encontrado" >&2
  exit 1
fi

# Obtener el ID del contenedor en ejecución
DB_CONTAINER=$(docker compose -f "${PROJECT_DIR}/docker-compose.dev.yml" ps -q "$DB_SERVICE")
if [[ -z "$DB_CONTAINER" ]]; then
  log "Error: Contenedor PostgreSQL no está corriendo"
  echo "[ERROR] Contenedor PostgreSQL no está activo" >&2
  exit 1
fi

# Extraer variables de entorno del contenedor (POSTGRES_DB y POSTGRES_USER)
DB_NAME=$(docker exec "$DB_CONTAINER" env | grep '^POSTGRES_DB=' | cut -d'=' -f2)
DB_USER=$(docker exec "$DB_CONTAINER" env | grep '^POSTGRES_USER=' | cut -d'=' -f2)

if [[ -z "$DB_NAME" || -z "$DB_USER" ]]; then
  log "Error: No se pudieron obtener DB_NAME o DB_USER del contenedor"
  echo "[ERROR] Variables de entorno PostgreSQL faltantes" >&2
  exit 1
fi

# -----------------------------------
# 3. Generar backup con pg_dump
# -----------------------------------
log "Ejecutando pg_dump (DB: $DB_NAME, USER: $DB_USER)"

docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" > "${BACKUP_PATH}" || {
  log "Error: pg_dump falló"
  echo "[ERROR] pg_dump falló" >&2
  exit 1
}

# Verificar que el archivo se haya creado y tenga tamaño > 0
if [[ ! -s "$BACKUP_PATH" ]]; then
  log "Error: backup vacío o inexistente"
  echo "[ERROR] Backup vacío" >&2
  exit 1
fi

# -----------------------------------
# 4. Generar checksum SHA256
# -----------------------------------
sha256sum "${BACKUP_PATH}" > "${SHA_FILE}"
SHA_SUM=$(awk '{print $1}' "${SHA_FILE}")
log "Checksum SHA256 generado: $SHA_SUM"

# -----------------------------------
# 5. Registro en log del backup
# -----------------------------------
log "Backup completado exitosamente"
log "Archivo: ${BACKUP_FILE}"
log "SHA256: $SHA_SUM"

# -----------------------------------
# 6. Retención automática (7‑4‑3)
# -----------------------------------
# 6.1 Mantener últimos 7 backups diarios
find "${BACKUP_DIR}" -maxdepth 1 -type f -name "backup_*.sql" -printf "%T@ %p\n" | sort -nr | tail -n +8 | cut -d' ' -f2- | while read -r old; do
  rm -f "$old" "${old}.sha256"
done

# 6.2 Mantener últimos 4 backups semanales (primer backup de cada semana)
# Se asume que los backups diarios están ya creados; conservamos el primero de cada semana
awk '{print strftime("%Y-%U", $1), $0}' <<< "$(find "${BACKUP_DIR}" -maxdepth 1 -type f -name "backup_*.sql" -printf "%T@ %p\n")" |
  sort -k1,1 -k2,2r | awk '!seen[$1]++ {print $2}' | tail -n +5 | while read -r wk; do
    rm -f "$wk" "${wk}.sha256"
done

# 6.3 Mantener últimos 3 backups mensuales (primer backup de cada mes)
awk '{print strftime("%Y-%m", $1), $0}' <<< "$(find "${BACKUP_DIR}" -maxdepth 1 -type f -name "backup_*.sql" -printf "%T@ %p\n")" |
  sort -k1,1 -k2,2r | awk '!seen[$1]++ {print $2}' | tail -n +4 | while read -r mo; do
    rm -f "$mo" "${mo}.sha256"
done

log "Política de retención aplicada (7‑4‑3)"

exit 0
