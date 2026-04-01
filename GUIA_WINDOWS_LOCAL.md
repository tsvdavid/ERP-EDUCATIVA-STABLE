# Procedimiento para Windows (Laptop Local)

Si estás trabajando en un entorno Windows en tu laptop, los conceptos de Git y Docker son exactamente los mismos, pero la forma de acceder a ellos a veces cambia ligeramente por tu terminal.

Sigue estos pasos para trabajar localmente en Windows y sincronizar con GitHub y tu Servidor VPS.

## 1. Descargar Cambios del Servidor a tu Laptop Windows
Si hiciste cambios en el servidor web (VPS) y quieres tenerlos en tu laptop:

1. Abre tu terminal en Windows (recomendado usar Git Bash o la terminal integrada de VS Code `Ctrl + Ñ`).
2. Ve a la carpeta de tu proyecto.
3. Ejecuta:
   ```bash
   git pull origin master
   ```
*(Con esto ya tendrás los cambios más recientes, como las guías que recién creamos y los ajustes de responsividad en las tablas).*

---

## 2. Aplicar Cambios en tu Entorno Local (Windows)
En Windows, dependiendo de cómo ejecutes el proyecto:

* **Escenario A (Con Node.js y npm directamente):** 
  Si levantas el frontend ejecutando `npm run dev`, los cambios se aplican automáticamente en tu navegador local (`http://localhost:5173`) sin necesidad de lanzar ningún comando nuevo.

* **Escenario B (Con Docker Desktop WSL2):**
  Si estás usando Docker Compose en tu laptop Windows para levantar todo el proyecto:
  ```bash
  docker compose build frontend
  docker compose up -d frontend
  ```

---

## 3. Subir Cambios de tu Laptop Windows a GitHub
Si desarrollas una nueva función en tu laptop Windows y quieres enviarla al mundo:

1. Modifica tus archivos.
2. Abre la terminal en VS Code y prepara los archivos:
   ```bash
   git add .
   ```
3. Guarda una versión (commit):
   ```cmd
   git commit -m "Descripción de los cambios que hice en mi laptop"
   ```
4. Sube al repositorio principal:
   ```bash
   git push origin master
   ```

**(Después de esto, tendrías que ir a la consola de SSH de tu Servidor Web VPS y ejecutar la `GUIA_DESPLIEGUE_DOCKER.md` para que la plataforma en vivo descargue tu nuevo trabajo).**
