# Prompt: Documentar arquitectura técnica de ERP-EDUCATIVA

## Objetivo

Generar la documentación técnica completa de la infraestructura del proyecto ERP-EDUCATIVA.

Al ejecutar este prompt, Antigravity deberá crear el archivo:

```
/home/sistemas/.gemini/antigravity/scratch/ERP-EDUCATIVA/docs/arquitectura-tecnica-erp.md
```

## Contenido esperado del documento `arquitectura-tecnica-erp.md`

1. **Diagrama de arquitectura** (texto plano) que muestre los componentes y puertos:

```
                 INTERNET
                     |
                     |
              Cloudflare Tunnel
                     |
                     |
              Frontend React
              Puerto 5174
                     |
                     |
              Backend Django
              Puerto 8000
                     |
        +------------+------------+
        |                         |
        v                         v

 PostgreSQL                 Redis
 Puerto 5432              Puerto 6379

 Base datos ERP           Cache/Sesiones
```

2. **Servicios Docker** – lista de servicios definidos en `docker-compose.dev.yml` (db, redis, backend, frontend, tunnel).

3. **Redes internas** – descripción de la red predeterminada de Docker Compose y cualquier red adicional.

4. **Volúmenes** – detalle de los volúmenes declarados (`db_data`, etc.) y su propósito.

5. **Variables de entorno** – tabla con las variables usadas por cada servicio (e.g., `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, variables del backend `.env`).

6. **Flujo de autenticación** – cómo el frontend se comunica con el backend, el backend verifica credenciales contra la base de datos y mantiene sesiones en Redis.

7. **Flujo de datos** – ruta de una petición típica: cliente → Cloudflare Tunnel → Frontend → Backend → PostgreSQL/Redis → respuesta.

8. **Dependencias entre servicios** – `backend` depende de `db` y `redis`; `frontend` depende de `backend`.

9. **Puertos expuestos** – tabla con puertos externos e internos para cada contenedor.

10. **Seguridad** – notas sobre SSL del túnel, aislamiento de contenedores, no exponer credenciales, uso de `.env`.

11. **Puntos críticos** – pérdida del contenedor `db`, corrupción de volúmenes, caída del túnel Cloudflare.

12. **Procedimiento de recuperación** – referencia a `docs/recuperacion-desastre.md` y pasos breves para restaurar los volúmenes y levantar los servicios.

---

## Instrucciones para Antigravity

Al ejecutar este prompt debe:

1. Leer el archivo `docker-compose.dev.yml` ubicado en el workspace oficial para extraer los nombres de los servicios, puertos, variables de entorno y volúmenes.
2. Generar el contenido estructurado descrito arriba y guardarlo en `docs/arquitectura-tecnica-erp.md`.
3. No tocar ningún código fuente, ni modificar Docker Compose, ni ejecutar migraciones, ni crear commits.
4. Devolver un mensaje indicando que el archivo ha sido creado con éxito.

---

## Restricciones

- No modificar código de `backend/` ni `frontend/`.
- No cambiar `docker-compose.dev.yml`.
- No ejecutar migraciones Django.
- No hacer `git commit` ni `git push`.
- Sólo crear/editar archivos bajo `docs/` y `prompts/`.
