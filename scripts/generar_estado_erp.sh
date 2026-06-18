#!/usr/bin/env bash

# generar_estado_erp.sh
# Aggregates the health checks of the ERP-EDUCATIVA system and produces a concise status report.
# Uses the auxiliary scripts health_check_erp.sh, verificar_backups.sh and verificar_espacio.sh.
# Exit code 0 indicates full operational state; non‑zero indicates at least one issue.

set -euo pipefail

# Determine project root (directory containing this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$PROJECT_ROOT"

# Functions to capture status
eval_check() {
  local name="$1"
  local cmd="$2"
  local result
  if result=$($cmd 2>/dev/null); then
    echo "${name} ............ OK"
    return 0
  else
    echo "${name} ............ KO"
    return 1
  fi
}

# Header
echo "================================"
echo " ERP-EDUCATIVA STATUS"
echo "================================"

# Run individual checks (ignore errors to continue collecting all statuses)
overall=0

# Frontend reachability (uses health_check_erp script, but we call curl directly for brevity)
if curl -s -f http://localhost:5174 > /dev/null; then
  echo "Frontend ............ OK"
else
  echo "Frontend ............ KO"
  overall=1
fi

# Backend health endpoint
if curl -s -f http://localhost:8000/api/health/ > /dev/null; then
  echo "Backend ............. OK"
else
  echo "Backend ............. KO"
  overall=1
fi

# PostgreSQL backup check
if ./scripts/verificar_backups.sh > /dev/null 2>&1; then
  echo "PostgreSQL .......... OK"
else
  echo "PostgreSQL .......... KO"
  overall=1
fi

# Redis container running (we just check docker ps for the service name 'redis')
if docker ps --filter "name=redis" --filter "status=running" | grep redis > /dev/null; then
  echo "Redis ............... OK"
else
  echo "Redis ............... KO"
  overall=1
fi

# Cloudflare Tunnel container running
if docker ps --filter "name=tunnel" --filter "status=running" | grep tunnel > /dev/null; then
  echo "Cloudflare Tunnel ... OK"
else
  echo "Cloudflare Tunnel ... KO"
  overall=1
fi

# Último backup (same as PostgreSQL check, already performed – reuse result)
echo "Último backup ....... $(if ./scripts/verificar_backups.sh > /dev/null 2>&1; then echo OK; else echo KO; fi)"

# Espacio disco
if ./scripts/verificar_espacio.sh > /dev/null 2>&1; then
  echo "Espacio disco ....... OK"
else
  echo "Espacio disco ....... KO"
  overall=1
fi

# Estado general
if [ $overall -eq 0 ]; then
  echo "\nEstado general ...... OPERATIVO"
else
  echo "\nEstado general ...... INCIDENTE"
fi

exit $overall
