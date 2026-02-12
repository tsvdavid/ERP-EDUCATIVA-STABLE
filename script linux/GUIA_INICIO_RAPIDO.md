# Guía de Inicialización Rápida - ERP EDUCATIVA

Este documento explica cómo inicializar y ejecutar el sistema ERP EDUCATIVA en este servidor. Existen principalmente dos formas de hacerlo: usando **Docker** (recomendado para pruebas rápidas y despliegue) o **Manualmente** (recomendado para desarrollo activo).

> [!IMPORTANT]
> **CONFIGURACIÓN DE PERMISOS (Paso Único):**
> Para que el usuario `sistemas` pueda ejecutar todo sin errores de permiso, ejecuta estos comandos **una sola vez** como root (o con sudo):
>
> 1.  Dar propiedad de la carpeta al usuario `sistemas`:
>     ```bash
>     sudo chown -R sistemas:sistemas /var/www/erpeducativa/ERP-EDUCATIVA
>     ```
>
> 2.  (Opcional) Permitir usar Docker sin sudo:
>     ```bash
>     sudo usermod -aG docker sistemas
>     # Luego cierra sesión y vuelve a entrar para aplicar cambios.
>     ```

---

## Opción 1: Ejecución con Docker (Recomendada)

Esta opción levanta todo el sistema (Base de datos, Backend, Frontend, Redis) en contenedores aislados. Es la forma más fácil de ver el sistema funcionando sin instalar dependencias en tu máquina.

### Requisitos
- Docker y Docker Compose instalados.

### Pasos
1. **Navega al directorio del proyecto:**
   ```bash
   cd /var/www/erpeducativa/ERP-EDUCATIVA
   ```

2. **Ejecuta el script de inicio (Modo Docker):**
   ```bash
   ./"script linux"/iniciar_docker.sh
   ```
   *Este script verificará el archivo `.env`, construirá los contenedores y ejecutará las migraciones automáticamente.*

---

## Opción 2: Ejecución Manual para Desarrollo

Si necesitas modificar el código frecuentemente, es mejor correr los servicios localmente.

### Requisitos del Sistema (Backend)
Para compilar las librerías gráficas (PDFs, gráficos) y de base de datos, necesitas instalar estas herramientas del sistema:

```bash
sudo apt update
sudo apt install -y build-essential python3-dev pkg-config libcairo2-dev libpango1.0-dev python3-venv
```

### Otros Requisitos
- Python 3.10+
- Node.js 18+ (o 20)
- PostgreSQL (y base de datos `erp_educativa` creada)

### Pasos
1. **Instalar Node.js (si no lo tienes):**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs
   ```

2. **Navega al directorio del proyecto:**
   ```bash
   cd /var/www/erpeducativa/ERP-EDUCATIVA
   ```

3. **Ejecuta el script de inicio (Modo Desarrollador):**
   ```bash
   ./"script linux"/iniciar_dev.sh
   ```
   *Este script levantará Django (backend) y React (Frontend) en paralelo en la misma terminal.*
   - El backend estará en: `http://localhost:8000`
   - El frontend estará en: `http://localhost:5173`

---

## Acceso desde Internet (Ngrok)

Si deseas compartir tu aplicación a través de internet, puedes usar el script de `ngrok` incluido.

1. **Abre una nueva terminal** (mantén corriendo el servidor Docker o Dev).
2. **Ejecuta el script:**
   ```bash
   ./"script linux"/iniciar_ngrok.sh
   ```
3. **Copia las direcciones HTTPS** que aparecen en pantalla.
   - Usa la dirección del Frontend para navegar.
   - **IMPORTANTE:** Debes actualizar el archivo `frontend/.env` con la dirección HTTPS que ngrok asignó al Backend (`VITE_API_URL=https://....ngrok-free.app/api`) y reiniciar el frontend.

---

## Notas Adicionales

- **Guía de Despliegue en VPS:**
  Para una configuración detallada de producción en un servidor Ubuntu (usando Nginx y Systemd nativos en lugar de Docker), consulta el archivo existente en la raíz:
  `GUIA_DESPLIEGUE_VPS.md`

- **Usuarios Admin:**
  Para crear un superusuario y acceder al panel de administración (`/admin`):
  ```bash
  # Con Docker
  docker compose exec backend python manage.py createsuperuser

  # Manual
  cd backend && source venv/bin/activate
  python manage.py createsuperuser
  ```
