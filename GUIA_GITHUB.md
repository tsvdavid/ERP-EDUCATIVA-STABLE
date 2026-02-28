# Procedimiento para Subir Cambios a GitHub

Este es el procedimiento estándar que debes realizar en tu **computadora local** cada vez que realices modificaciones (o correcciones) al código y desees respaldarlas y prepararlas para enviarlas al servidor de producción.

## Pasos

1. **Abre tu terminal** y asegúrate de estar en la carpeta principal del proyecto (donde se encuentra la carpeta `frontend`, `backend`, etc.).
   
   Ejemplo: `C:\var\www\erpeducativa\ERP-EDUCATIVA` o `~/ERP-EDUCATIVA`

2. **Prepara todos los archivos modificados** para ser "empaquetados". Esto agrega cualquier archivo creado, modificado o eliminado:
   ```bash
   git add .
   ```
   *(Nota: El punto `.` significa "añadir todo". Si solo quieres subir un archivo específico, usarías `git add ruta/al/archivo.jsx`)*

3. **Crea el paquete de cambios (Commit)** con un mensaje descriptivo que te ayude a saber qué hiciste en esta versión:
   ```bash
   git commit -m "Describe aquí el cambio (ej. Fix: tabla responsiva en tramites)"
   ```

4. **Sube los cambios** al repositorio en la nube (GitHub):
   ```bash
   git push origin master
   ```
   *(Si tu rama principal no se llama `master` sino `main`, el comando sería `git push origin main`)*

¡Listo! Con esto, tu código está a salvo en GitHub y disponible para ser descargado por el servidor de entorno de producción.
