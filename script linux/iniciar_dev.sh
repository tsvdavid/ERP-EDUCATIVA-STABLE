#!/bin/bash

# Script de inicio en Modo Desarrollador
# Este script inicia Backend (Django) y Frontend (Vite) localmente sin Docker.
# Requiere Python 3, Node.js y PostgreSQL instalados.

# Colores y variables
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directorio raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}--- Iniciando Modo Desarrollador ---${NC}"
cd "$PROJECT_ROOT"

# Función para verificar comandos
check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: '$1' no está instalado. Por favor instala las dependencias.${NC}"
        # Sugerir install
        if [ "$1" == "npm" ]; then
            echo "Ejecuta: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs"
        elif [ "$1" == "python3" ]; then
             echo "Ejecuta: sudo apt install python3"
        fi
        exit 1
    fi
}

check_cmd "python3"
check_cmd "npm"
check_cmd "psql"
check_cmd "redis-cli"

# Función para manejar el cierre (Ctrl+C)
cleanup() {
    echo -e "\n${BLUE}Deteniendo servicios...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM

# --- 1. INICIAR BACKEND ---
echo -e "${GREEN}[Backend] Configurando Django...${NC}"
cd "$PROJECT_ROOT/backend"

# Limpieza de entorno virtual roto (comun si python3-venv falto antes)
if [ -d "venv" ] && [ ! -f "venv/bin/activate" ]; then
    echo -e "${BLUE}Detectado venv incompleto. Recreando...${NC}"
    rm -rf venv
fi

# Crear venv si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    if ! python3 -m venv venv; then
         echo -e "${RED}Error al crear venv. Falta python3-venv?${NC}"
         echo "Prueba ejecutar: sudo apt install python3-venv"
         exit 1
    fi
fi

# Activar venv
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al activar entorno virtual.${NC}"
    exit 1
fi

# Instalar dependencias SIEMPRE (para asegurar) y mostrar output
echo "Instalando/verificando dependencias Python..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Error instalando dependencias Python (pip).${NC}"
    exit 1
fi

echo -e "${BLUE}Verificando backend/.env...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}⚠️ Creado backend/.env de ejemplo para desarrollo local...${NC}"
    cat <<EOF > .env
DEBUG=True
SECRET_KEY=clave_secreta_local
ALLOWED_HOSTS=*
DB_NAME=erp_educativa
DB_USER=postgres
DB_PASSWORD=postgrespw
DB_HOST=localhost
REDIS_URL=redis://localhost:6379/0
EOF
fi

echo -e "${BLUE}Ejecutando migraciones de Base de Datos...${NC}"
python manage.py migrate

# Iniciar servidor en segundo plano
echo -e "${GREEN}[Backend] Iniciando daphne en http://0.0.0.0:8000 ...${NC}"
daphne -b 0.0.0.0 -p 8000 config.asgi:application &
BACKEND_PID=$!

# --- 2. INICIAR FRONTEND ---
echo -e "${GREEN}[Frontend] Configurando React/Vite...${NC}"
cd "$PROJECT_ROOT/frontend"

# Instalar node_modules SIEMPRE (para asegurar vite) y mostrar output
echo "Instalando/verificando dependencias NPM..."
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}Error instalando dependencias NPM.${NC}"
    exit 1
fi

echo -e "${BLUE}Verificando frontend/.env...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}⚠️ Creado frontend/.env de ejemplo...${NC}"
    echo "VITE_API_URL=http://localhost:8000/api" > .env
fi

# Iniciar servidor en segundo plano
echo -e "${GREEN}[Frontend] Iniciando servidor en http://localhost:5173 ...${NC}"
# No necesitamos export VITE_API_URL si ya está en .env, pero lo dejamos por si acaso
export VITE_API_URL="/api"
npm run dev -- --host &
FRONTEND_PID=$!

# --- 3. ESPERAR ---
echo -e "${BLUE}--- Todos los servicios iniciados ---${NC}"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Presiona Ctrl+C para detener todo."

wait
