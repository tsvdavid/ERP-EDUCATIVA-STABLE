-- Hardening 2.1: Global RLS Provisioning
-- Author: Antigravity Architect

DO $$
DECLARE
    r RECORD;
    table_list TEXT[] := ARRAY[
        'academic_academicyear', 'academic_academicperiod', 'academic_course', 'academic_subject', 
        'academic_enrollment', 'academic_evaluationcategory', 'academic_grade', 'academic_attendance', 
        'academic_observation', 'academic_classschedule', 'treasury_paymentmethod', 'treasury_paymentconcept', 
        'treasury_studentaccount', 'treasury_invoice', 'treasury_charge', 'treasury_invoicedetail', 
        'treasury_payment', 'treasury_creditnote', 'treasury_debitnote', 'accounting_fiscalyear', 
        'accounting_account', 'accounting_journalentry', 'accounting_journalitem', 'accounting_accountingconfig', 
        'accounting_bank', 'accounting_bankaccount', 'accounting_fixedasset', 'accounting_depreciation', 
        'purchases_supplier', 'purchases_purchaseinvoice', 'purchases_purchaseitem', 'purchases_withholding', 
        'purchases_purchasecreditnote', 'purchases_purchasedebitnote', 'purchases_purchaseliquidation', 
        'purchases_purchaseliquidationitem', 'helpdesk_servicecatalog', 'helpdesk_workflow', 'helpdesk_passstep', 
        'helpdesk_ticket', 'helpdesk_ticketsurvey', 'helpdesk_scheduledjob', 'helpdesk_ticketcomment', 
        'helpdesk_ticketattachment', 'privacy_policyversion', 'privacy_consentrecord', 'privacy_treatmentactivity', 
        'privacy_arcorequest', 'privacy_databreach', 'procedures_proceduretemplate', 'procedures_studentrequest', 
        'health_medicalrecord', 'health_decerecord', 'health_medicalvisit', 'health_decevisit', 
        'health_behaviorrecord', 'health_behaviorcase', 'health_casefollowup', 'health_studentriskprofile', 
        'health_alertrule'
    ];
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY table_list
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', table_name);
        
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_policy ON %I', table_name);
        
        -- Strict Policy: If app.current_tenant is not set, current_setting() will throw an error if not using the 'true' flag as second arg.
        -- But user wants it to fail correctly.
        EXECUTE format('
            CREATE POLICY tenant_isolation_policy ON %I
            AS PERMISSIVE
            FOR ALL
            TO PUBLIC
            USING (institution_id = current_setting(''app.current_tenant'')::integer)
            WITH CHECK (institution_id = current_setting(''app.current_tenant'')::integer)
        ', table_name);
        
        RAISE NOTICE 'RLS Activado para tabla: %', table_name;
    END LOOP;
END $$;
