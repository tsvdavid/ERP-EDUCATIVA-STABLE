import os
import django
import sys
from django.db.models import F

# Setup Django environment
sys.path.append('/var/www/erpeducativa/ERP-EDUCATIVA/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import Invoice, InvoiceDetail, Payment, Customer
from accounting.models import JournalEntry, JournalItem

def run_diagnostics():
    print("--- INICIO DE DIAGNÓSTICO DE INTEGRIDAD MULTI-TENANT ---\n")

    # 1. Invoices sin institution_id
    null_invoices = Invoice.objects.filter(institution__isnull=True)
    print(f"[1] Facturas sin institución: {null_invoices.count()}")
    for inv in null_invoices[:5]:
        print(f"    - ID: {inv.id}, Numero: {inv.number}")

    # 2. Payments sin institution_id
    null_payments = Payment.objects.filter(institution__isnull=True)
    print(f"[2] Pagos sin institución: {null_payments.count()}")
    for pay in null_payments[:5]:
        print(f"    - ID: {pay.id}, Invoice ID: {pay.invoice_id}")

    # 3. JournalItems cruzados (Institución de Item != Institución de Asiento)
    crossed_items = JournalItem.objects.select_related('journal_entry').exclude(institution_id=F('journal_entry__institution_id'))
    print(f"[3] JournalItems cruzados (Item Inst != Entry Inst): {crossed_items.count()}")
    for item in crossed_items[:5]:
        print(f"    - Item ID: {item.id}, Item Inst: {item.institution_id}, Entry Inst: {item.journal_entry.institution_id}")

    # 4. Invoices con Clientes de otro Tenant
    crossed_customers = Invoice.objects.filter(customer__isnull=False).select_related('customer').exclude(institution_id=F('customer__institution_id'))
    print(f"[4] Facturas con clientes cruzados (Inv Inst != Cust Inst): {crossed_customers.count()}")
    for inv in crossed_customers[:5]:
        print(f"    - Inv ID: {inv.id}, Inv Inst: {inv.institution_id}, Cust Inst: {inv.customer.institution_id}")

    # 4b. Invoices sin cliente
    missing_customers = Invoice.objects.filter(customer__isnull=True)
    print(f"[4b] Facturas sin cliente asignado: {missing_customers.count()}")
    for inv in missing_customers[:5]:
        print(f"    - Inv ID: {inv.id}, Numero: {inv.number}")

    # 5. InvoiceDetails sin institución o cruzados
    null_details = InvoiceDetail.objects.filter(institution__isnull=True)
    print(f"[5] Detalles de factura sin institución: {null_details.count()}")
    
    crossed_details = InvoiceDetail.objects.select_related('invoice').exclude(institution_id=F('invoice__institution_id'))
    print(f"[6] Detalles de factura cruzados (Detail Inst != Inv Inst): {crossed_details.count()}")
    for det in crossed_details[:5]:
        print(f"    - Detail ID: {det.id}, Detail Inst: {det.institution_id}, Inv Inst: {det.invoice.institution_id}")

    print("\n--- FIN DEL DIAGNÓSTICO ---")

if __name__ == "__main__":
    run_diagnostics()
