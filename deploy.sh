#!/bin/bash

# Script de Despliegue Automático para ERP Educativo
# Ejecutar en el servidor Ubuntu: bash deploy.sh

echo "--- Iniciando Despliegue Automatizado ---"

# 1. Definir directorio
APP_DIR="/var/www/erpeducativa"

if [ ! -d "$APP_DIR" ]; then
    echo "Directorio no existe. Creando $APP_DIR..."
    mkdir -p $APP_DIR
    cd $APP_DIR
    echo "Clonando repositorio..."
    # Asume que ya configuraste la SSH key en GitHub
    git clone git@github.com:tsvdavid/ERP-EDUCATIVA.git .
else
    cd $APP_DIR
    echo "Directorio existe. Bajando últimos cambios..."
    git pull origin master
fi

# 2. Verificar .env (Importante seguridad)
if [ ! -f "backend/.env" ]; then
    echo "⚠️ ALERTA: No se encontró backend/.env. Creando uno de ejemplo..."
    echo "DEBUG=False" > backend/.env
    echo "SECRET_KEY=cambiar_esto_en_produccion" >> backend/.env
    echo "ALLOWED_HOSTS=*" >> backend/.env
    echo "DB_NAME=erp_educativa" >> backend/.env
    echo "DB_USER=postgres" >> backend/.env
    echo "DB_PASSWORD=postgrespw" >> backend/.env
    echo "DB_HOST=db" >> backend/.env
    echo "REDIS_URL=redis://redis:6379/0" >> backend/.env
    echo "Por favor edita backend/.env con tus credenciales reales."
fi

# 3. Levantar Contenedores
echo "Construyendo y levantando contenedores de Producción..."
# Usamos el archivo prod
docker compose -f docker-compose.prod.yml up -d --build

# 4. Migraciones y Estáticos
echo "Ejecutando migraciones de base de datos..."
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

echo "Recolectando archivos estáticos..."
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

echo "--- Despliegue Finalizado Exitosamente ---"
echo "Tu ERP debería estar corriendo en el puerto 80 (HTTP)."
