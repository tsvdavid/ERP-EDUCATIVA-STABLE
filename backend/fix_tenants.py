import os
import django
import sys

# Setup Django environment
sys.path.append('/var/www/erpeducativa/ERP-EDUCATIVA/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import Invoice, InvoiceDetail, Payment
from accounting.models import JournalItem

def run_fix():
    print("--- INICIO DE REPARACIÓN DE INTEGRIDAD MULTI-TENANT ---\n")

    # 1. Alinear InvoiceDetails
    print("Alineando InvoiceDetails con sus facturas...")
    count = 0
    for det in InvoiceDetail.objects.select_related('invoice').all():
        if det.institution_id != det.invoice.institution_id:
            det.institution_id = det.invoice.institution_id
            det.save()
            count += 1
    print(f"InvoiceDetails alineados: {count}")

    # 2. Alinear Payments
    print("Alineando Payments con sus facturas...")
    count = 0
    for pay in Payment.objects.select_related('invoice').all():
        if pay.institution_id != pay.invoice.institution_id:
            pay.institution_id = pay.invoice.institution_id
            pay.save()
            count += 1
    print(f"Payments alineados: {count}")

    # 3. Alinear JournalItems
    print("Alineando JournalItems con sus asientos...")
    count = 0
    for item in JournalItem.objects.select_related('journal_entry').all():
        if item.institution_id != item.journal_entry.institution_id:
            item.institution_id = item.journal_entry.institution_id
            item.save()
            count += 1
    print(f"JournalItems alineados: {count}")

    # 4. Limpiar facturas sin cliente (Orfanas/Pruebas fallidas)
    print("Eliminando facturas sin cliente...")
    deleted_count, _ = Invoice.objects.filter(customer__isnull=True).delete()
    print(f"Facturas eliminadas: {deleted_count}")

    print("\n--- REPARACIÓN COMPLETADA ---")

if __name__ == "__main__":
    run_fix()
