#!/usr/bin/env bash

# generar_reporte_diario.sh
# Genera un informe diario de estado del ERP-EDUCATIVA y lo guarda en docs/auditorias/estado_YYYY-MM-DD.md

set -euo pipefail

# Ruta del proyecto (asume que este script está en ./scripts)
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OUTPUT_DIR="${PROJECT_ROOT}/docs/auditorias"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)
REPORT_FILE="${OUTPUT_DIR}/estado_${DATE}.md"

# Crear directorio si no existe
mkdir -p "${OUTPUT_DIR}"

# Ejecutar checks y capturar salida y código de retorno
health_out=$("${PROJECT_ROOT}/scripts/health_check_erp.sh" 2>&1) || health_rc=$?
health_rc=${health_rc:-0}

backup_out=$("${PROJECT_ROOT}/scripts/verificar_backups.sh" 2>&1) || backup_rc=$?
backup_rc=${backup_rc:-0}

espacio_out=$("${PROJECT_ROOT}/scripts/verificar_espacio.sh" 2>&1) || espacio_rc=$?
espacio_rc=${espacio_rc:-0}

# Docker PS (todos los contenedores)
docker_ps_all=$(docker compose -f "${PROJECT_ROOT}/docker-compose.dev.yml" ps 2>/dev/null || true)

# Docker stats (sin stream, formato tabla)
docker_stats=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || true)

# Espacio libre del servidor donde está el proyecto
disk_usage=$(df -h .)

# Determinar estado general
if (( health_rc != 0 || backup_rc != 0 || espacio_rc != 0 )); then
  overall="CRÍTICO"
else
  overall="OPERATIVO"
fi

# Generar reporte Markdown
{
  echo "# Estado Diario ERP-EDUCATIVA"
  echo ""
  echo "Fecha: $DATE"
  echo "Hora: $TIME"
  echo ""
  echo "## Resumen"
  echo "Estado General: $overall"
  echo ""
  echo "## Health Check"
  echo "\`\`\`"
  echo "$health_out"
  echo "\`\`\`"
  echo ""
  echo "## Backups"
  echo "\`\`\`"
  echo "$backup_out"
  echo "\`\`\`"
  echo ""
  echo "## Espacio en Disco"
  echo "\`\`\`"
  echo "$espacio_out"
  echo "\`\`\`"
  echo ""
  echo "## Docker PS"
  echo "\`\`\`"
  echo "$docker_ps_all"
  echo "\`\`\`"
  echo ""
  echo "## Docker Stats"
  echo "\`\`\`"
  echo "$docker_stats"
  echo "\`\`\`"
  echo ""
  echo "## Uso del Sistema (df -h)"
  echo "\`\`\`"
  echo "$disk_usage"
  echo "\`\`\`"
} > "${REPORT_FILE}"

# Mostrar información de salida
echo "Reporte generado: ${REPORT_FILE}"
stat -c "Tamaño: %s bytes" "${REPORT_FILE}"
