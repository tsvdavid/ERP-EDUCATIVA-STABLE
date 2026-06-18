# CONTROL OPERATIVO ERP-EDUCATIVA

## ESTADO DEL SISTEMA

| Componente | Estado |
|------------|--------|
| Frontend   | 🟢 |
| Backend    | 🟢 |
| PostgreSQL | 🟢 |
| Redis      | 🟢 |
| Cloudflare | 🟢 |

> **Nota**: Los estados deben actualizarse manualmente según los resultados de los checks (`docker ps`, `docker logs`, `curl` health checks, etc.).

---

## OPERACIONES DIARIAS

- [ ] Revisar servicios Docker (`docker ps`).
- [ ] Confirmar que el último backup se haya generado (`ls -lh backups/` y revisar `backup.log`).
- [ ] Revisar logs de contenedores y aplicación (`docker logs backend`, `docker logs frontend`).
- [ ] Ejecutar health check del API: `curl -I http://localhost:8000/api/health/`.

---

## OPERACIONES SEMANALES

- [ ] Revisar espacio en disco (`df -h`).
- [ ] Revisar errores y advertencias en los logs de aplicación y de Docker.
- [ ] Actualizar dependencias de backend (`pip list --outdated`) y frontend (`npm outdated`).
- [ ] Verificar que los volúmenes persisten correctamente (`docker volume ls`).

---

## OPERACIONES MENSUALES

- [ ] Ejecutar auditoría completa usando `prompts/audit_full_erp_prompt.md`.
- [ ] Probar restauración siguiendo `docs/recuperacion-desastre.md` (restaurar el último backup en un entorno de pruebas).
- [ ] Revisar y actualizar políticas de seguridad (revisar variables `.env`, tokens, permisos de archivo).
- [ ] Validar healthchecks de Docker (añadirlos si aún no están definidos).
- [ ] Documentar cualquier cambio de infraestructura y actualizar la documentación correspondiente.

---

## RECOMENDACIONES TÉCNICAS ADICIONALES (para futura revisión)

1. **Redis en autenticación**: Confirmar la configuración real en `settings.py`. Si `SESSION_ENGINE` usa cache, Redis sirve para sesiones; si se emplean JWT, Redis actúa solo como cache.
2. **Ingress del Cloudflare Tunnel**: Verificar si el túnel dirige directamente al frontend o a un Nginx/Backend intermedio.
3. **Exposición de PostgreSQL**: Considerar cambiar `ports` a `expose` en `docker-compose.dev.yml` para producción.
4. **Healthchecks Docker**: Implementar healthchecks para PostgreSQL, Redis y Backend en futuros ajustes.

---

*Este documento forma parte del conjunto de documentación operativa oficial del proyecto ERP-EDUCATIVA.*
