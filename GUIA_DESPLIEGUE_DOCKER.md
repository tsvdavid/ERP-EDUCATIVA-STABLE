# Procedimiento para Actualizar / Subir Cambios (Despliegue)

Una vez que tengas código nuevo (o hayas descargado actualizaciones con `git pull` en el servidor), este es el procedimiento consolidado y seguro para aplicar los cambios a los entornos mediante Docker. Este procedimiento reemplaza el uso del script automático (`deploy.sh`) para evitar interrupciones no deseadas en servicios de terceros.

## Pasos

### 1. Reconstruir el Entorno Local (Opcional)
Si estás probando los cambios en tu propia computadora usando Docker (y no con Node.js directamente), ejecuta estos comandos desde la carpeta raíz del proyecto para actualizar el servicio del frontend:

```bash
docker compose build frontend
docker compose up -d frontend
```

---

*(Los siguientes pasos se ejecutan desde la línea de comandos SSH, en la consola de tu servidor VPS / Entorno de Producción)*

### 2. Reconstruir el Entorno de Producción (Web)
Para construir la nueva versión del contenedor y subirla de forma limpia usando tu archivo de configuración de producción:

```bash
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### 3. Refrescar la Caché de Red (Nginx)
Nginx suele mantener atascada en memoria la dirección interna (`IP`) del contenedor viejo. Para evitar el mensaje de "Error 502 (Bad Gateway)", siempre debemos pedirle que reinicie y busque los nuevos contenedores:

```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### 4. Reconectar el Túnel Exterior (Cloudflare / Ngrok)
Al utilizar los comandos del paso 2 indicando el archivo de producción, Docker a menudo apaga servicios que estaban descritos en el archivo base (como tu conector de dominio exterior). Para recuperarlo y asegurar que la plataforma sea accesible desde internet y teléfonos móviles, enciéndelo nuevamente con su comando base:

```bash
docker compose up -d tunnel
```

Con estos 4 pasos, garantizas una actualización fluida de la aplicación sin desconectar accidentalmente componentes de red externos.
