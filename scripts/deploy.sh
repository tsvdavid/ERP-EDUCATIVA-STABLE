#!/bin/bash

# Script de Despliegue Automático para Eduka360 (Versión Actualizada)
# Ubicación: scripts/deploy.sh

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}--- Iniciando Despliegue Automatizado ---${NC}"

# 1. Definir directorio (Auto-detectado)
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"

echo "Directorio detectado: $APP_DIR"
cd "$APP_DIR"

# Verificar si estamos en un repositorio git
if [ -d ".git" ]; then
    echo "Actualizando código desde Git..."
    git pull origin master
else
    echo "Aviso: No se detectó un repositorio Git. Continuando con los archivos locales."
fi

# 2. Verificar .env (Importante seguridad)
if [ ! -f "backend/.env" ]; then
    echo -e "${RED}⚠️ ALERTA: No se encontró backend/.env. Creando uno de ejemplo...${NC}"
    cat <<EOF > backend/.env
DEBUG=False
SECRET_KEY=$(openssl rand -hex 24 2>/dev/null || echo "cambiar_esto_en_produccion")
ALLOWED_HOSTS=*
DB_NAME=erp_educativa
DB_USER=postgres
DB_PASSWORD=postgrespw
DB_HOST=db
REDIS_URL=redis://redis:6379/0
EOF
    echo "Por favor edita backend/.env con tus credenciales reales."
fi

if [ ! -f "frontend/.env" ]; then
    echo -e "${RED}⚠️ ALERTA: No se encontró frontend/.env. Creando uno de ejemplo...${NC}"
    echo "VITE_API_URL=https://tu-dominio.com/api" > frontend/.env
    echo "Por favor edita frontend/.env con tu dominio real."
fi

# 3. Levantar Contenedores
echo -e "${GREEN}Construyendo y levantando contenedores de Producción...${NC}"
# Usamos el archivo prod si existe, si no el default
if [ -f "docker-compose.prod.yml" ]; then
    docker compose -f docker-compose.prod.yml up -d --build
else
    docker compose up -d --build
fi

# 4. Migraciones y Estáticos
echo "Ejecutando migraciones de base de datos..."
COMPOSE_FILE=$( [ -f "docker-compose.prod.yml" ] && echo "-f docker-compose.prod.yml" || echo "" )
docker compose $COMPOSE_FILE run --rm backend python manage.py migrate

echo "Recolectando archivos estáticos..."
docker compose $COMPOSE_FILE run --rm backend python manage.py collectstatic --noinput

echo "Reiniciando servicios adicionales (Nginx)..."
docker compose $COMPOSE_FILE restart nginx 2>/dev/null || true

echo "Limpiando imágenes antiguas de Docker..."
docker image prune -af

echo -e "${GREEN}--- Despliegue Finalizado Exitosamente ---${NC}"
echo "El sistema debería estar disponible en los puertos configurados (80/443)."
