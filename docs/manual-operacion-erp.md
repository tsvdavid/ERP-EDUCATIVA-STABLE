# Manual Operativo ERP-EDUCATIVA

## 1. Arquitectura del sistema

```
Usuario
 |
 Cloudflare Tunnel
 |
 Frontend React
 |
 Backend Django
 |
 PostgreSQL
 |
 Redis
```

## 2. Inicio del sistema

**Comandos:**

```bash
docker compose -f docker-compose.dev.yml up -d
```

**Validaciones:**

```bash
docker ps
curl http://localhost:8000/api/health/
```

## 3. Detención segura

```bash
docker compose -f docker-compose.dev.yml down
```

## 4. Backup

**Explicación:** Utilizar el script oficial de backup.

**Ejemplo:**

```bash
./scripts/script_backup_postgres.sh
```

**Resultado esperado:**

```
backups/
 ├── backup_YYYY_MM_DD.sql
 └── backup_YYYY_MM_DD.sql.sha256
```

## 5. Restauración

Seguir el procedimiento descrito en la documentación de recuperación:

```
/docs/recuperacion-desastre.md
```

## 6. Auditoría

Utilizar los prompts operativos para generar auditorías:

- `prompts/audit_full_erp_prompt.md`
- `prompts/disaster_recovery_validation_prompt.md`

## 7. Monitoreo

Revisar los siguientes elementos regularmente:

- Logs de contenedores: `docker logs <service>`
- Log de backups: `backups/backup.log`
- Estado del disco: `df -h`

## 8. Seguridad

- No subir backups a repositorios Git.
- Proteger archivos `.env` y cualquier credencial.
- Mantener copias de seguridad en medios externos seguros.
- Revisar y restringir accesos a los contenedores y a la base de datos.

## 9. Checklist mensual

- [ ] Backup correcto
- [ ] Restauración probada
- [ ] Disco revisado
- [ ] Logs revisados
- [ ] Docker actualizado
- [ ] Auditoría ejecutada
