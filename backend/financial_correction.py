from accounting.models import JournalEntry, JournalItem, Account
from users.models import User, Institution
from django.db import transaction
from decimal import Decimal
import logging

def run_corrections():
    # 1. Configuración de Entorno
    audit_user = User.objects.get(username='admin') # O el usuario auditor
    audit_tenant = Institution.objects.get(id=9)
    
    with transaction.atomic():
        # 2. Crear Cuenta de Ajuste Técnico si no existe
        adj_account, created = Account.objects.get_or_create(
            code='9.9.01',
            institution=audit_tenant,
            defaults={
                'name': 'Ajuste de Integridad Técnica (Corrección)',
                'account_type': 'EQUITY', # O una categoría neutral
                'description': 'Cuenta puente para regularización de asientos descuadrados de auditoría.'
            }
        )
        if created: print("Cuenta 9.9.01 creada.")

        # 3. Mapeo de Ajustes
        # ID: (AccountCode_to_Debit, Amount_to_Debit, Description)
        corrections = {
            8: ('5.2.04.03', Decimal('300.00'), 'Ajuste Gasto Limpieza - Factura 555'),
            9: ('5.1.01.01', Decimal('2000.00'), 'Ajuste Costo Uniformes - Factura 12345'),
            10: ('5.2.05.01', Decimal('4000.00'), 'Ajuste Suministros Papelería - Factura 8888')
        }

        for eid, (expense_code, amount, desc) in corrections.items():
            try:
                original = JournalEntry.objects.get(id=eid)
                
                # Marcar Original
                original.is_unbalanced = True
                original.save()

                # Crear Asiento de Ajuste (Auditable)
                adjustment = JournalEntry.objects.create(
                    institution=original.institution,
                    date=original.date,
                    description=f"RE-PROCESO: {desc} (Corrige Asiento #{eid})",
                    reference=original.reference,
                    state='POSTED', # Asentado para integridad
                    entry_type='ADJUSTMENT',
                    adjustment_for=original,
                    created_by=audit_user
                )

                # Debit: The missing expense
                expense_acc = Account.objects.get(code=expense_code, institution=original.institution)
                JournalItem.objects.create(
                    journal_entry=adjustment,
                    account=expense_acc,
                    debit=amount,
                    credit=0,
                    description=f"Complemento de gasto omitido en #{eid}",
                    institution=original.institution
                )

                # Credit: The Bridge/Correction Account
                # Para que el balance global cuadre, necesitamos una contrapartida.
                # Como el original tenía IVA(D) y Proveedores(C), la diferencia era un D missing.
                # Aquí Damos D al Gasto y C a la puente.
                JournalItem.objects.create(
                    journal_entry=adjustment,
                    account=adj_account,
                    debit=0,
                    credit=amount,
                    description=f"Contrapartida técnica de balanceo por #{eid}",
                    institution=original.institution
                )
                
                print(f"Ajuste para #{eid} creado: {adjustment.id}")

            except Exception as e:
                print(f"Error procesando #{eid}: {e}")

