#!/usr/bin/env bash

# verificar_espacio.sh
# Checks available disk space on the host where ERP-EDUCATIVA runs.
# Returns non‑zero exit code if any partition exceeds 85% usage.

set -euo pipefail

THRESHOLD=85

# Find the filesystem where the project directory resides
PROJECT_DIR="$(pwd)"
FS=$(df -P "$PROJECT_DIR" | tail -1 | awk '{print $1}')

# Get usage percentage
USAGE=$(df -P "$PROJECT_DIR" | tail -1 | awk '{print $5}' | tr -d "%")

if [ "$USAGE" -ge "$THRESHOLD" ]; then
  echo "Disk usage on $FS is ${USAGE}% (threshold ${THRESHOLD}%)."
  exit 1
else
  echo "Disk usage on $FS is ${USAGE}% (within threshold)."
  exit 0
fi
