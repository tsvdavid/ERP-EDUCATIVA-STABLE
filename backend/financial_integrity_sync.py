from treasury.models import InvoiceDetail, Payment, CreditNote, DebitNote, Invoice
from accounting.models import JournalItem, JournalEntry, Depreciation, FixedAsset
from users.models import Institution
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def sync_financial_integrity():
    audit_tenant = Institution.objects.get(ruc='0000000000000')
    
    with transaction.atomic():
        # --- TREASURY ---
        print("Rescatando Treasury (InvoiceDetail)...")
        for obj in InvoiceDetail.objects.filter(institution__isnull=True):
            if obj.invoice:
                obj.institution = obj.invoice.institution
            else:
                obj.institution = audit_tenant
                obj.is_orphaned = True
                logger.warning(f"Orphaned InvoiceDetail ID {obj.id} assigned to audit tenant.")
            obj.save()

        print("Rescatando Treasury (Payment)...")
        for obj in Payment.objects.filter(institution__isnull=True):
            if obj.invoice:
                obj.institution = obj.invoice.institution
            else:
                obj.institution = audit_tenant
                obj.is_orphaned = True
            obj.save()

        print("Rescatando Treasury (Notes)...")
        for obj in CreditNote.objects.filter(institution__isnull=True):
            obj.institution = obj.invoice.institution if obj.invoice else audit_tenant
            if not obj.invoice: obj.is_orphaned = True
            obj.save()
        for obj in DebitNote.objects.filter(institution__isnull=True):
            obj.institution = obj.invoice.institution if obj.invoice else audit_tenant
            if not obj.invoice: obj.is_orphaned = True
            obj.save()

        # --- ACCOUNTING ---
        print("Rescatando Accounting (JournalItem)...")
        for obj in JournalItem.objects.filter(institution__isnull=True):
            if obj.journal_entry:
                obj.institution = obj.journal_entry.institution
            else:
                obj.institution = audit_tenant
                obj.is_orphaned = True
            obj.save()

        print("Rescatando Accounting (Depreciation)...")
        for obj in Depreciation.objects.filter(institution__isnull=True):
            if obj.asset:
                obj.institution = obj.asset.institution
            else:
                obj.institution = audit_tenant
                obj.is_orphaned = True
            obj.save()

        # --- VALIDATION ---
        print("\n--- VALIDACIÓN DE BALANCES CONTABLES ---")
        unbalanced = []
        for entry in JournalEntry.objects.all():
            if not entry.is_balanced:
                unbalanced.append(f"Entry ID {entry.id} ({entry.description}) is UNBALANCED: Debit={entry.total_debit}, Credit={entry.total_credit}")
        
        if unbalanced:
            print(f"ALERTA: Se encontraron {len(unbalanced)} asientos descuadrados:")
            for msg in unbalanced[:10]: print(f"  - {msg}")
        else:
            print("Integridad de balances: OK (Todos los asientos cuadran)")

    print("\nSincronización de Hardening 2.0 (Fase Financiera) completada.")

if __name__ == "__main__":
    sync_financial_integrity()
