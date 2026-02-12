#!/bin/bash

# Script de inicio con Docker
# Este script levanta todos los servicios utilizando Docker Compose.

# Obtener la ruta absoluta del directorio del proyecto (un nivel arriba de este script)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "--- Iniciando ERP EDUCATIVA con Docker ---"
echo "Directorio del proyecto: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Verificar si Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker no parece estar funcionando. Asegúrate de que el servicio esté activo."
    exit 1
fi

echo "Levantando contenedores (Frontend, Backend, DB, Redis)..."
# Usamos --build para asegurar que se reflejen cambios recientes
docker compose up --build
