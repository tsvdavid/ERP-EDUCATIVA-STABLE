# Prompt: Auditoría Integral de Operación y Continuidad ERP-EDUCATIVA

## Objetivo

Realizar una auditoría completa del entorno ERP-EDUCATIVA para validar:

* Integridad de backups.
* Funcionamiento del cron.
* Capacidad real de restauración.
* Estado de Docker.
* Estado de PostgreSQL.
* Estado de Redis.
* Estado de Cloudflare Tunnel.
* Consistencia de la documentación.
* Riesgos operativos.
* Riesgos de seguridad.
* Madurez de continuidad del negocio.

Generar el informe:

```

docs/auditorias/auditoria_integral_erp_$(date +%Y-%m-%d).md
```

---

## Alcance

Analizar exclusivamente:

* `scripts/`
* `docs/`
* `prompts/`
* `docker-compose.dev.yml`
* `backend/.env` (solo estructura, sin exponer secretos)
* `backups/`

No modificar código.

No modificar Docker.

No ejecutar migraciones.

No crear commits.

No realizar push.

---

## Validaciones requeridas

### 1. Inventario de servicios

Identificar:

* db
* redis
* backend
* frontend
* tunnel

Generar tabla:

| Servicio | Estado | Imagen | Dependencias |
| -------- | ------ | ------ | ------------ |
|          |        |        |              |

---

### 2. Auditoría de backups

Verificar:

* existencia de backups
* tamaño de backups
* integridad SHA256
* retención 7-4-3
* permisos de archivos

Ejecutar validación:

```
sha256sum -c backups/*.sha256
```

Documentar resultados.

---

### 3. Auditoría de cron

Verificar:

* existencia de `install_backup_cron.sh`
* existencia de tarea programada
* formato correcto del cron
* duplicados

Evaluar riesgo de múltiples ejecuciones.

---

### 4. Auditoría de PostgreSQL

Validar:

* contenedor activo
* volumen persistente
* espacio utilizado
* accesibilidad mediante `docker exec`

Generar sección:

**Estado de Base de Datos**

---

### 5. Auditoría de Redis

Verificar:

* contenedor activo
* consumo de memoria
* conectividad

Determinar:

* cache solamente
  o
* cache + sesiones

según configuración detectada.

---

### 6. Auditoría de Cloudflare Tunnel

Validar:

* contenedor activo
* presencia de `TUNNEL_TOKEN`
* logs recientes
* errores de conexión

Generar diagnóstico.

---

### 7. Auditoría de monitoreo

Verificar existencia y funcionamiento de:

* `health_check_erp.sh`
* `verificar_backups.sh`
* `verificar_espacio.sh`
* `generar_estado_erp.sh`
* `dashboard_estado_erp.sh`
* `generar_reporte_diario.sh`

Generar matriz:

| Script | Existe | Ejecutable | Observaciones |
| ------ | ------ | ---------- | ------------- |
|        |        |            |               |

---

### 8. Auditoría documental

Validar coherencia entre:

* `manual-operacion-erp.md`
* `arquitectura-tecnica-erp.md`
* `recuperacion-desastre.md`
* `backup-operacion.md`
* `centro-operaciones.md`
* `seguridad-operativa.md`
* `matriz-riesgos.md`
* `inventario-activos.md`

Identificar:

* documentación duplicada
* documentación faltante
* referencias rotas

---

### 9. Simulación de desastre

Evaluar escenarios:

#### Escenario 1

Pérdida de PostgreSQL

#### Escenario 2

Caída de Redis

#### Escenario 3

Caída del túnel Cloudflare

#### Escenario 4

Servidor completo fuera de línea

Calificar:

* Tiempo estimado de recuperación (RTO)
* Pérdida máxima de datos (RPO)

---

### 10. Seguridad

Evaluar:

* exposición de puertos
* protección de secretos
* permisos de backups
* riesgos Docker
* riesgos Cloudflare

Asignar:

* BAJO
* MEDIO
* ALTO
* CRÍTICO

---

### 11. Score de madurez operativa

Asignar puntuación:

| Área          | Puntuación |
| ------------- | ---------- |
| Backup        | 0-10       |
| Restauración  | 0-10       |
| Monitoreo     | 0-10       |
| Seguridad     | 0-10       |
| Documentación | 0-10       |
| Continuidad   | 0-10       |

Calcular score total sobre 100.

---

### 12. Recomendaciones

Separar:

#### Acciones críticas (24 horas)

#### Acciones recomendadas (7 días)

#### Mejoras estratégicas (30 días)

---

## Resultado esperado

Crear:

```

docs/auditorias/auditoria_integral_erp_YYYY-MM-DD.md
```

con hallazgos, evidencias, riesgos, puntuación y plan de mejora.

No realizar cambios automáticos.

Solo documentar.
