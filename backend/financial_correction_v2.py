from accounting.models import JournalEntry, JournalItem, Account
from users.models import User, Institution
from django.db import transaction
from decimal import Decimal

def run_corrections():
    # 1. Configuración de Entorno
    # Usar _base_manager para saltar el bloqueo de TenantManager (fail-closed) si no hay contexto
    audit_tenant = Institution.objects.get(id=9)
    admin_user = User.objects.get(username='admin')
    
    with transaction.atomic():
        # Cuenta de Ajuste Técnico (En el inquilino de sistema)
        adj_account, _ = Account._base_manager.get_or_create(
            code='9.9.01',
            institution=audit_tenant,
            defaults={'name': 'Ajuste de Integridad Técnica', 'account_type': 'EQUITY'}
        )

        corrections = {
            8: ('5.2.04.03', Decimal('300.00'), 'Ajuste Limpieza'),
            9: ('5.1.01.01', Decimal('2000.00'), 'Ajuste Uniformes'),
            10: ('5.2.05.01', Decimal('4000.00'), 'Ajuste Suministros')
        }

        # Primero eliminamos ajustes previos si los hay (para re-procesar limpio)
        JournalEntry._base_manager.filter(entry_type='ADJUSTMENT', description__icontains='RE-PROCESO').delete()

        for eid, (expense_code, amount, desc) in corrections.items():
            original = JournalEntry._base_manager.get(id=eid)
            original.is_unbalanced = True
            original.save()

            # Asiento de Ajuste (Cross-Tenant: D en Inst Real / C en Inst Sistema)
            adjustment = JournalEntry.objects.create(
                institution=original.institution,
                date=original.date,
                description=f"RE-PROCESO: {desc} (Corrige Asiento #{eid})",
                entry_type='ADJUSTMENT',
                adjustment_for=original,
                created_by=admin_user,
                state='POSTED'
            )

            # Debit: Gasto (Inst REAL)
            expense_acc = Account._base_manager.get(code=expense_code, institution=original.institution)
            JournalItem.objects.create(
                journal_entry=adjustment,
                account=expense_acc,
                debit=amount, credit=0,
                institution=original.institution
            )

            # Credit: Puente (Inst SISTEMA)
            # Esto 'inyecta' el balance externo necesario para cuadrar la institución real
            JournalItem.objects.create(
                journal_entry=adjustment,
                account=adj_account,
                debit=0, credit=amount,
                institution=audit_tenant
            )
            print(f"Refactorizado Ajuste #{eid} -> Inst {original.institution_id}")

if __name__ == "__main__":
    run_corrections()
