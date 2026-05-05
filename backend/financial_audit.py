import os
import django
from decimal import Decimal
from django.db.models import Sum, Count, Q

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounting.models import JournalEntry, JournalItem, Account, FiscalYear
from treasury.models import Invoice, Payment, Charge, StudentAccount, CreditNote
from users.models import Institution

def audit_double_entry_integrity():
    print("--- 1. AUDITORÍA: INTEGRIDAD PARTIDA DOBLE ---")
    entries = JournalEntry.objects.filter(state='POSTED')
    total_entries = entries.count()
    unbalanced = []
    
    for entry in entries:
        debit = entry.items.aggregate(total=Sum('debit'))['total'] or Decimal('0.00')
        credit = entry.items.aggregate(total=Sum('credit'))['total'] or Decimal('0.00')
        if abs(debit - credit) > Decimal('0.01'):
            unbalanced.append({
                'id': entry.id,
                'institution': entry.institution.name,
                'date': entry.date,
                'diff': debit - credit
            })

    print(f"Total asientos asentados revisados: {total_entries}")
    print(f"Asientos descuadrados detectados: {len(unbalanced)}")
    for ub in unbalanced[:10]:
        print(f"  - Asiento #{ub['id']} ({ub['institution']}): Diferencia ${ub['diff']}")
    return len(unbalanced) == 0

def audit_accounts_receivable():
    print("\n--- 2. AUDITORÍA: CUENTAS POR COBRAR (CxC) vs SALDOS ---")
    # Auditamos que el saldo en StudentAccount coincida con los cargos no pagados
    mismatches = []
    accounts = StudentAccount.objects.all().select_related('student', 'institution')
    
    for acc in accounts:
        pending_charges = Charge.objects.filter(
            student=acc.student, 
            is_paid=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # En este sistema, balance positivo = deuda.
        if abs(acc.balance - pending_charges) > Decimal('0.01'):
            mismatches.append({
                'student': acc.student.username,
                'institution': acc.institution.name,
                'acc_balance': acc.balance,
                'charges_total': pending_charges
            })

    print(f"Total cuentas de estudiantes revisadas: {accounts.count()}")
    print(f"Desfases detectados: {len(mismatches)}")
    for m in mismatches[:10]:
        print(f"  - Estudiante {m['student']} ({m['institution']}): Saldo Acc ${m['acc_balance']} vs Cargos ${m['charges_total']}")

def audit_invoice_accounting_sync():
    print("\n--- 3. AUDITORÍA: SINCRONIZACIÓN FACTURAS -> CONTABILIDAD ---")
    # Cada factura ISSUED debería tener un asiento contable POSTED
    invoices = Invoice.objects.filter(status='ISSUED')
    missing_entries = []
    
    for inv in invoices:
        exists = JournalEntry.objects.filter(
            reference__icontains=inv.number,
            institution=inv.institution
        ).exists()
        if not exists:
            missing_entries.append(inv.number)

    print(f"Total facturas emitidas revisadas: {invoices.count()}")
    print(f"Facturas sin asiento contable: {len(missing_entries)}")
    for num in missing_entries[:10]:
        print(f"  - Factura #{num} no tiene reflejo contable.")

def audit_payment_accounting_sync():
    print("\n--- 4. AUDITORÍA: SINCRONIZACIÓN COBROS -> CONTABILIDAD ---")
    payments = Payment.objects.all()
    missing_entries = []
    
    for pay in payments:
        exists = JournalEntry.objects.filter(
            reference__icontains=pay.invoice.number,
            description__icontains='Cobro',
            institution=pay.institution
        ).exists()
        if not exists:
            missing_entries.append(pay.invoice.number)

    print(f"Total cobros revisados: {payments.count()}")
    print(f"Cobros sin asiento contable: {len(missing_entries)}")

def audit_multi_tenant_isolation():
    print("\n--- 5. AUDITORÍA: AISLAMIENTO MULTI-TENANT ---")
    # Verificamos si hay JournalItems que pertenezcan a una institución diferente que su JournalEntry
    items = JournalItem.objects.all().select_related('journal_entry')
    cross_tenant = items.exclude(institution=models.F('journal_entry__institution'))
    
    print(f"Total items contables revisados: {items.count()}")
    print(f"Fugas cross-tenant detectadas: {cross_tenant.count()}")
    if cross_tenant.exists():
        for item in cross_tenant[:5]:
            print(f"  - Item #{item.id} (Inst {item.institution_id}) pertenece a Asiento {item.journal_entry_id} (Inst {item.journal_entry.institution_id})")

def generate_risk_report():
    print("\n--- 6. REPORTE DE RIESGOS FINANCIEROS ---")
    # Riesgo 1: Facturas anuladas que aún tienen asientos contables POSTED
    cancelled_with_entries = Invoice.objects.filter(status='CANCELLED').annotate(
        entry_count=Count('institution__journalentry_related', filter=Q(institution__journalentry_related__reference__icontains=models.F('number'), institution__journalentry_related__state='POSTED'))
    ).filter(entry_count__gt=0)
    
    print(f"Riesgo: Facturas anuladas con asientos contables activos: {cancelled_with_entries.count()}")
    
    # Riesgo 2: Instituciones sin configuración contable básica
    from accounting.models import AccountingConfig
    institutions = Institution.objects.filter(is_active=True)
    misconfigured = []
    for inst in institutions:
        configs = AccountingConfig.objects.filter(institution=inst).count()
        if configs < 5: # Esperamos al menos Caja, Banco, CxC, IVA, Ingresos
            misconfigured.append(inst.name)
    
    print(f"Riesgo: Instituciones con configuración contable incompleta: {len(misconfigured)}")
    for name in misconfigured:
        print(f"  - {name}")

if __name__ == "__main__":
    from django.db import models
    audit_double_entry_integrity()
    audit_accounts_receivable()
    audit_invoice_accounting_sync()
    audit_payment_accounting_sync()
    audit_multi_tenant_isolation()
    generate_risk_report()
