-- Optimizacion de Rendimiento RLS 3.1 (CORREGIDO)
-- Creacion de indices compuestos estrategicos para acelerar el filtrado multi-tenant

-- 1. Academico: Calificaciones (Filtro por fecha y tenant)
DROP INDEX IF EXISTS idx_composite_academic_grade_inst_date;
CREATE INDEX idx_composite_academic_grade_inst_date 
ON academic_grade (institution_id, date DESC);

-- 2. Contabilidad: Items de Asiento (Filtro por asiento y tenant)
DROP INDEX IF EXISTS idx_composite_accounting_journalitem_inst_entry;
CREATE INDEX idx_composite_accounting_journalitem_inst_entry 
ON accounting_journalitem (institution_id, journal_entry_id);

-- 3. Auditoria: Logs (Filtro por tiempo y tenant)
DROP INDEX IF EXISTS idx_composite_core_actionlog_inst_time;
CREATE INDEX idx_composite_core_actionlog_inst_time 
ON core_actionlog (institution_id, timestamp DESC);

-- 4. Finanzas: Facturas (Filtro por estado y tenant)
DROP INDEX IF EXISTS idx_composite_treasury_invoice_inst_status;
CREATE INDEX idx_composite_treasury_invoice_inst_status 
ON treasury_invoice (institution_id, status);

-- 5. Salud: Visitas Medicas (Filtro por fecha y tenant)
DROP INDEX IF EXISTS idx_composite_health_medicalvisit_inst_date;
CREATE INDEX idx_composite_health_medicalvisit_inst_date 
ON health_medicalvisit (institution_id, date DESC);

-- Nota: El orden (institution_id, <field>) es critico.
-- RLS inyecta la condicion 'institution_id = X' en cada query, 
-- permitiendo que Postgres use este prefijo para descartar datos de otros inquilinos inmediatamente.
