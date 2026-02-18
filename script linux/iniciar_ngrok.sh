#!/bin/bash

# Script para iniciar Ngrok exponiendo Backend y Frontend
# Requiere 'ngrok' instalado en el sistema.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$DIR/ngrok.yml"

echo "--- Iniciando Tunel Ngrok ---"
echo "Exponiendo puertos: 8000 (Backend) y 5173 (Frontend)"
echo "Configuración: $CONFIG_FILE"
echo ""
echo "IMPORTANTE:"
echo "1. Usa la URL HTTPS generada para el **Frontend (puerto 5173)**."
echo "2. Ya NO necesitas configurar nada manualmente (el proxy se encarga)."
echo "3. Abre esa URL en tu móvil."
echo "-----------------------------"

ngrok start --all --config "$CONFIG_FILE"
