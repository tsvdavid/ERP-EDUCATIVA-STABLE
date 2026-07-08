
DO $$
DECLARE
    r RECORD;
    tbl TEXT;
    read_policy TEXT;
    write_policy TEXT;
BEGIN
    -- 1) Tablas tenant directas: tienen institution_id físico
    FOR r IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    ) LOOP
        tbl := r.tablename;

        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = tbl
              AND column_name = 'institution_id'
        ) THEN
            read_policy := format('rls_read_direct__%s', tbl);
            write_policy := format('rls_write_direct__%s', tbl);

            EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);
            EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', tbl);

            EXECUTE format('DROP POLICY IF EXISTS %I ON %I', read_policy, tbl);
            EXECUTE format('DROP POLICY IF EXISTS %I ON %I', write_policy, tbl);

            EXECUTE format(
                'CREATE POLICY %I ON %I FOR SELECT USING (
                    (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
                    OR institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
                )',
                read_policy,
                tbl
            );

            EXECUTE format(
                'CREATE POLICY %I ON %I FOR ALL USING (
                    (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
                    OR institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
                ) WITH CHECK (
                    (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
                    OR institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
                )',
                write_policy,
                tbl
            );
        END IF;
    END LOOP;

    -- 2) Caso especial: users_institution (sin institution_id)
    read_policy := 'rls_read_indirect__users_institution';
    write_policy := 'rls_write_indirect__users_institution';

    EXECUTE 'ALTER TABLE users_institution ENABLE ROW LEVEL SECURITY';
    EXECUTE 'ALTER TABLE users_institution FORCE ROW LEVEL SECURITY';

    EXECUTE format('DROP POLICY IF EXISTS %I ON users_institution', read_policy);
    EXECUTE format('DROP POLICY IF EXISTS %I ON users_institution', write_policy);

    EXECUTE format(
        'CREATE POLICY %I ON users_institution FOR SELECT USING (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
        )',
        read_policy
    );

    EXECUTE format(
        'CREATE POLICY %I ON users_institution FOR ALL USING (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
        ) WITH CHECK (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
        )',
        write_policy
    );

    -- 3) Tabla crítica indirecta: knowledge_knowledgearticle
    read_policy := 'rls_read_indirect__knowledge_knowledgearticle';
    write_policy := 'rls_write_indirect__knowledge_knowledgearticle';

    EXECUTE 'ALTER TABLE knowledge_knowledgearticle ENABLE ROW LEVEL SECURITY';
    EXECUTE 'ALTER TABLE knowledge_knowledgearticle FORCE ROW LEVEL SECURITY';

    EXECUTE format('DROP POLICY IF EXISTS %I ON knowledge_knowledgearticle', read_policy);
    EXECUTE format('DROP POLICY IF EXISTS %I ON knowledge_knowledgearticle', write_policy);

    EXECUTE format(
        'CREATE POLICY %I ON knowledge_knowledgearticle FOR SELECT USING (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR EXISTS (
                SELECT 1
                FROM knowledge_knowledgecategory kc
                WHERE kc.id = knowledge_knowledgearticle.category_id
                  AND kc.institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
            )
        )',
        read_policy
    );

    EXECUTE format(
        'CREATE POLICY %I ON knowledge_knowledgearticle FOR ALL USING (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR EXISTS (
                SELECT 1
                FROM knowledge_knowledgecategory kc
                WHERE kc.id = knowledge_knowledgearticle.category_id
                  AND kc.institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
            )
        ) WITH CHECK (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR EXISTS (
                SELECT 1
                FROM knowledge_knowledgecategory kc
                WHERE kc.id = knowledge_knowledgearticle.category_id
                  AND kc.institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
            )
        )',
        write_policy
    );

    -- 4) Tabla crítica indirecta: subscriptions_subscriptionmodule
    read_policy := 'rls_read_indirect__subscriptions_subscriptionmodule';
    write_policy := 'rls_write_indirect__subscriptions_subscriptionmodule';

    EXECUTE 'ALTER TABLE subscriptions_subscriptionmodule ENABLE ROW LEVEL SECURITY';
    EXECUTE 'ALTER TABLE subscriptions_subscriptionmodule FORCE ROW LEVEL SECURITY';

    EXECUTE format('DROP POLICY IF EXISTS %I ON subscriptions_subscriptionmodule', read_policy);
    EXECUTE format('DROP POLICY IF EXISTS %I ON subscriptions_subscriptionmodule', write_policy);

    EXECUTE format(
        'CREATE POLICY %I ON subscriptions_subscriptionmodule FOR SELECT USING (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR EXISTS (
                SELECT 1
                FROM subscriptions_subscription s
                WHERE s.id = subscriptions_subscriptionmodule.subscription_id
                  AND s.institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
            )
        )',
        read_policy
    );

    EXECUTE format(
        'CREATE POLICY %I ON subscriptions_subscriptionmodule FOR ALL USING (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR EXISTS (
                SELECT 1
                FROM subscriptions_subscription s
                WHERE s.id = subscriptions_subscriptionmodule.subscription_id
                  AND s.institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
            )
        ) WITH CHECK (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR EXISTS (
                SELECT 1
                FROM subscriptions_subscription s
                WHERE s.id = subscriptions_subscriptionmodule.subscription_id
                  AND s.institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
            )
        )',
        write_policy
    );

    -- 5) Tabla crítica indirecta: subscriptions_subscriptionpayment
    read_policy := 'rls_read_indirect__subscriptions_subscriptionpayment';
    write_policy := 'rls_write_indirect__subscriptions_subscriptionpayment';

    EXECUTE 'ALTER TABLE subscriptions_subscriptionpayment ENABLE ROW LEVEL SECURITY';
    EXECUTE 'ALTER TABLE subscriptions_subscriptionpayment FORCE ROW LEVEL SECURITY';

    EXECUTE format('DROP POLICY IF EXISTS %I ON subscriptions_subscriptionpayment', read_policy);
    EXECUTE format('DROP POLICY IF EXISTS %I ON subscriptions_subscriptionpayment', write_policy);

    EXECUTE format(
        'CREATE POLICY %I ON subscriptions_subscriptionpayment FOR SELECT USING (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR EXISTS (
                SELECT 1
                FROM subscriptions_subscription s
                WHERE s.id = subscriptions_subscriptionpayment.subscription_id
                  AND s.institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
            )
        )',
        read_policy
    );

    EXECUTE format(
        'CREATE POLICY %I ON subscriptions_subscriptionpayment FOR ALL USING (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR EXISTS (
                SELECT 1
                FROM subscriptions_subscription s
                WHERE s.id = subscriptions_subscriptionpayment.subscription_id
                  AND s.institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
            )
        ) WITH CHECK (
            (COALESCE(NULLIF(current_setting(''app.rls_mode'', true), ''''), ''tenant'') = ''global_admin'')
            OR EXISTS (
                SELECT 1
                FROM subscriptions_subscription s
                WHERE s.id = subscriptions_subscriptionpayment.subscription_id
                  AND s.institution_id = COALESCE(NULLIF(current_setting(''app.current_tenant'', true), ''''), ''0'')::integer
            )
        )',
        write_policy
    );
END $$;
