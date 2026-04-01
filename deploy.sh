#!/bin/bash

# Wrapper de compatibilidad para deploy.sh
# Redirige a la nueva ubicación en scripts/deploy.sh

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts"

if [ -f "$SCRIPTS_DIR/deploy.sh" ]; then
    bash "$SCRIPTS_DIR/deploy.sh" "$@"
else
    echo "Error: No se encontró scripts/deploy.sh"
    exit 1
fi
