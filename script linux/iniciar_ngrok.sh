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
echo "1. Copia la URL HTTPS generada para el Backend (puerto 8000)."
echo "2. Pégala en 'frontend/.env' en VITE_API_URL."
echo "3. Reinicia tu servidor frontend si es necesario."
echo "-----------------------------"

ngrok start --all --config "$CONFIG_FILE"
