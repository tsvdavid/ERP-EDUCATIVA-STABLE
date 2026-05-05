
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        -- Verificar si la tabla tiene la columna institution_id
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = r.tablename AND column_name = 'institution_id') THEN
            EXECUTE 'ALTER TABLE ' || r.tablename || ' ENABLE ROW LEVEL SECURITY;';
            EXECUTE 'ALTER TABLE ' || r.tablename || ' FORCE ROW LEVEL SECURITY;';
            EXECUTE 'DROP POLICY IF EXISTS tenant_isolation_policy ON ' || r.tablename || ';';
            
            -- Política Robusta: Maneja NULL y VACÍO convirtiéndolos en 0 (denegado)
            EXECUTE 'CREATE POLICY tenant_isolation_policy ON ' || r.tablename || ' USING (institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer);';
            EXECUTE 'CREATE POLICY tenant_isolation_policy ON ' || r.tablename || ' WITH CHECK (institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer);';
        
        ELSIF r.tablename = 'users_institution' THEN
            -- Caso especial: Institution filtra por su propia ID
            EXECUTE 'ALTER TABLE ' || r.tablename || ' ENABLE ROW LEVEL SECURITY;';
            EXECUTE 'ALTER TABLE ' || r.tablename || ' FORCE ROW LEVEL SECURITY;';
            EXECUTE 'DROP POLICY IF EXISTS tenant_isolation_policy ON ' || r.tablename || ';';
            
            EXECUTE 'CREATE POLICY tenant_isolation_policy ON ' || r.tablename || ' USING (id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer);';
        END IF;
    END LOOP;
END $$;
