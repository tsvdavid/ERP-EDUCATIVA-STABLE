# Matriz de Riesgos ERP-EDUCATIVA

| Riesgo                     | Impacto | Probabilidad | Nivel   | Acción / Mitigación                              |
|----------------------------|---------|--------------|---------|---------------------------------------------------|
| Corrupción PostgreSQL      | Alto    | Media        | Crítico | Backup diario; validar integridad con SHA256      |
| Pérdida del servidor       | Alto    | Baja         | Alto    | Plan de recuperación desastre (docs/recuperacion-desastre.md) |
| Caída Cloudflare Tunnel    | Medio   | Baja         | Medio   | Monitorear estado del túnel; reiniciar contenedor `tunnel` |
| Disco lleno                | Alto    | Media        | Alto    | Monitoreo diario de espacio (`df -h`); alertas de uso >80% |
| Credenciales expuestas     | Crítico | Baja         | Alto    | Rotación inmediata de secretos; auditoría de .env   |
| Fallo del backup script    | Alto    | Media        | Crítico | Revisar logs de backup (`backups/backup.log`), pruebas de restauración mensuales |
| Vulnerabilidad en Docker   | Medio   | Baja         | Medio   | Mantener imágenes actualizadas; usar versiones mínimas de vulnerabilidad |
| Ataque a la API            | Alto    | Media        | Crítico | Implementar rate‑limiting, WAF en Cloudflare, auditorías de seguridad |
| Pérdida de logs            | Medio   | Baja         | Medio   | Rotación y copia de logs a almacenamiento externo |

**Interpretación del nivel**:
- **Crítico**: requiere acción inmediata y monitorización constante.
- **Alto**: debe incluirse en los procesos de revisión semanal.
- **Medio**: se controla mediante revisiones mensuales.

**Actualización**: La matriz debe revisarse al menos una vez al trimestre o cuando se introduzcan cambios significativos en la infraestructura.
