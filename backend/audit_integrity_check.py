import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection, models
from core.models import TenantModel
from accounting.models import JournalEntry
from django.apps import apps
from decimal import Decimal

def audit_report():
    print("=== AUDITORÍA SENIOR DE SEGURIDAD Y DATOS (EDUKA360) ===\n")

    # 1. Verificar RLS en la Base de Datos
    print("1. Verificando Row-Level Security (RLS) en PostgreSQL...")
    with connection.cursor() as cursor:
        cursor.execute("SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' AND rowsecurity = true;")
        rls_tables = cursor.fetchall()
        if not rls_tables:
            print("  [!] ADVERTENCIA: No hay tablas con rowsecurity = true en 'public'.")
        else:
            print(f"  [OK] Se encontraron {len(rls_tables)} tablas con RLS activo:")
            for t in rls_tables:
                print(f"    - {t[0]}")

    # 2. Integridad de Modelos (TenantModel)
    print("\n2. Escaneando Integridad de TenantModel...")
    tenant_models = [m for m in apps.get_models() if issubclass(m, TenantModel)]
    null_violations = []
    
    for model in tenant_models:
        null_count = model.objects.filter(institution__isnull=True).count()
        if null_count > 0:
            null_violations.append((model.__name__, null_count))
            
    if not null_violations:
        print(f"  [OK] 0 registros huérfanos detectados en {len(tenant_models)} modelos analizados.")
    else:
        print("  [!] FALLO DE INTEGRIDAD: Registros sin institución detectados:")
        for name, count in null_violations:
            print(f"    - {name}: {count} nulos")

    # 3. Consistencia Financiera (Contabilidad)
    print("\n3. Validando Balances Contables...")
    unbalanced_entries = []
    for entry in JournalEntry.objects.all():
        if not entry.is_balanced:
            unbalanced_entries.append(entry.id)
            
    if not unbalanced_entries:
        print("  [OK] Todos los asientos contables están balanceados.")
    else:
        print(f"  [!] RIESGO CRÍTICO: {len(unbalanced_entries)} asientos descuadrados:")
        print(f"    IDs: {unbalanced_entries[:10]}")

    # 4. Simulación de Error Humano (Bypass)
    print("\n4. Simulando Error Humano (Bypass de TenantManager)...")
    try:
        # Intentar acceder a todos los registros ignorando el filtro por defecto
        # Nota: TenantManager filtra por defecto. Veremos si podemos forzar .all() sin contexto.
        from django.conf import settings
        # Simulamos que no hay tenant en el hilo actual
        from core.middleware import _thread_locals
        setattr(_thread_locals, 'tenant_id', None)
        
        # Si el manager no tiene filtro por defecto cuando tenant_id es None, devolverá todo.
        # Un sistema "Hardened" debería devolver nada o fallar.
        sample_model = JournalEntry
        count = sample_model.objects.all().count()
        print(f"  Resultado de Model.objects.all() sin contexto: {count} registros.")
        if count > 0:
            print("  [!] OBSERVACIÓN: Se devolvieron registros sin contexto de tenant. El aislamiento depende del Middleware.")
        else:
            print("  [OK] El sistema devuelve 0 registros o falla cuando no hay contexto de tenant.")

    except Exception as e:
        print(f"  [OK] Error esperado al intentar bypass: {e}")

if __name__ == "__main__":
    audit_report()
