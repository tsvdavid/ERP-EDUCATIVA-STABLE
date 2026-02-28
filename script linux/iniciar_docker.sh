#!/bin/bash

# Script de inicio con Docker
# Este script levanta todos los servicios utilizando Docker Compose.

# Obtener la ruta absoluta del directorio del proyecto (un nivel arriba de este script)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "--- Iniciando Eduka360 con Docker ---"
echo "Directorio del proyecto: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Verificar si Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker no parece estar funcionando. Asegúrate de que el servicio esté activo."
    exit 1
fi

echo "Configurando variables de entorno si faltan..."
if [ ! -f "backend/.env" ]; then
    echo "⚠️ Creando backend/.env de ejemplo..."
    cat <<EOF > backend/.env
DEBUG=True
SECRET_KEY=clave_secreta_local
ALLOWED_HOSTS=*
DB_NAME=erp_educativa
DB_USER=postgres
DB_PASSWORD=postgrespw
DB_HOST=db
REDIS_URL=redis://redis:6379/0
EOF
fi

if [ ! -f "frontend/.env" ]; then
    echo "⚠️ Creando frontend/.env de ejemplo..."
    echo "VITE_API_URL=http://localhost:8000/api" > frontend/.env
fi

echo "Levantando contenedores (Frontend, Backend, DB, Redis)..."
# Usamos --build para asegurar que se reflejen cambios recientes
docker compose up -d --build

echo "Ejecutando migraciones de base de datos..."
docker compose exec backend python manage.py migrate

echo "--- Eduka360 levantado localmente con Docker Compose ---"
