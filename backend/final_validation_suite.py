import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.apps import apps
from django.db import connection, transaction
from core.models import TenantModel
from accounting.models import JournalEntry, JournalItem, Account
from core.thread_context import set_current_tenant_id, clear_current_tenant
from django.db.models import Sum
from users.models import User

def validate():
    results = {}
    print("=== RE-SUITE DE VALIDACIÓN: HARDENING 2.1 (FIXED) ===\n")

    # 1. SEGURIDAD: Fail-Closed
    print("1. Validando Fail-Closed del TenantManager...")
    clear_current_tenant()
    count = JournalEntry.objects.all().count()
    results['bypass_security'] = 'PASSED (Bloqueado)' if count == 0 else f'FAILED (Leak: {count} registros)'
    print(f"   Resultado: {results['bypass_security']}")

    # 2. CONSISTENCIA: Huérfanos
    print("\n2. Escaneando registros sin institución...")
    total_orphans = 0
    for m in [m for m in apps.get_models() if issubclass(m, TenantModel)]:
        total_orphans += m._base_manager.filter(institution__isnull=True).count()
    results['orphans_check'] = 'PASSED' if total_orphans == 0 else f'FAILED ({total_orphans} huérfanos)'
    print(f"   Resultado: {results['orphans_check']}")

    # 3. CONTABILIDAD: Integridad de Institución
    print("\n3. Validando Balance Institucional (Neto)...")
    try:
        summary = JournalItem._base_manager.filter(institution_id=1).aggregate(
            total_debit=Sum('debit'), total_credit=Sum('credit')
        )
        diff = abs((summary['total_debit'] or 0) - (summary['total_credit'] or 0))
        results['accounting_net'] = 'PASSED' if diff == 0 else f'FAILED (Diff: {diff})'
    except Exception as e:
        results['accounting_net'] = f'ERROR: {e}'
    print(f"   Resultado: {results['accounting_net']}")

    # 4. CARGA: Stress Test
    print("\n4. Ejecutando Stress Test (5000 registros)...")
    admin_user = User.objects.get(username='admin')
    start_time = time.time()
    for i in range(10):
        set_current_tenant_id(i + 1)
        objs = [JournalEntry(
            institution_id=i+1, created_by=admin_user, 
            description=f"STRESS_TEST_{j}", date="2024-04-21"
        ) for j in range(500)]
        JournalEntry.objects.bulk_create(objs)
    end_time = time.time()
    clear_current_tenant()
    results['load_test'] = f'PASSED ({end_time - start_time:.2f}s)'
    print(f"   Resultado: {results['load_test']}")

    # 5. RLS
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM pg_policies WHERE policyname = 'tenant_isolation_policy';")
        policy_count = cursor.fetchone()[0]
        results['rls_global'] = 'PASSED' if policy_count >= 60 else f'FAILED ({policy_count})'
    print(f"\n5. RLS Global: {results['rls_global']}")

    # VEREDICTO
    ready = all('PASSED' in str(v) for v in results.values())
    print(f"\n{'='*40}")
    print(f"VEREDICTO FINAL PRODUCCIÓN: {'SI' if ready else 'NO'}")
    print(f"{'='*40}")

if __name__ == '__main__':
    validate()
