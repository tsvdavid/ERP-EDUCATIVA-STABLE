# Guía de Inicialización Rápida - ERP EDUCATIVA

Este documento explica cómo inicializar y ejecutar el sistema ERP EDUCATIVA. Se recomienda usar la nueva carpeta `scripts/` para todas las operaciones.

---

## Opción 1: Ejecución con Docker (Recomendada)

Levanta todo el sistema (BD, Backend, Frontend, Redis) en contenedores.

### Pasos
1. **Navega al directorio del proyecto:**
   ```bash
   cd /var/www/erpeducativa/ERP-EDUCATIVA
   ```

2. **Ejecuta el script de inicio:**
   ```bash
   bash scripts/iniciar_docker.sh
   ```

---

## Opción 2: Ejecución Manual (Desarrollo)

Para modificar el código frecuentemente sin reconstruir contenedores.

### Pasos
1. **Navega al directorio del proyecto:**
   ```bash
   cd /var/www/erpeducativa/ERP-EDUCATIVA
   ```

2. **Ejecuta el script de desarrollo:**
   ```bash
   bash scripts/iniciar_dev.sh
   ```
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:5173`

---

## Despliegue en Producción

Para actualizar el servidor con los últimos cambios de Git:

```bash
bash scripts/deploy.sh
```

---

## Acceso desde Internet (Ngrok)

Para pruebas externas temporales:

1. **Abre una nueva terminal.**
2. **Ejecuta:**
   ```bash
   bash scripts/iniciar_ngrok.sh
   ```

---

## Notas de Administración

- **Crear Superusuario (Docker):**
  ```bash
  docker compose exec backend python manage.py createsuperuser
  ```

- **Rutas de Scripts:**
  Todos los scripts han sido actualizados para detectar automáticamente la ruta del proyecto, por lo que pueden ejecutarse desde cualquier ubicación, aunque se recomienda hacerlo desde la raíz del proyecto.
