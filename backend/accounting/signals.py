from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from treasury.models import Invoice, Payment
from accounting.models import JournalEntry, JournalItem, Account, FiscalYear, AccountingConfig
from django.core.exceptions import ObjectDoesNotExist

# Helper to find standard accounts (Legacy/Fallback)
def get_account_by_code_prefix(institution, code_start):
    try:
        return Account.objects.filter(
            institution=institution, 
            code__startswith=code_start, 
            is_active=True
        ).order_by('code').first()
    except:
        return None

# New Helper using Configuration
def get_configured_account(institution, key, default_prefix=None):
    """
    Tries to find the account via AccountingConfig.
    If not found, falls back to searching by prefix (legacy behavior) to ensure backward compatibility.
    """
    try:
        config = AccountingConfig.objects.get(institution=institution, key=key)
        return config.account
    except AccountingConfig.DoesNotExist:
        if default_prefix:
            return get_account_by_code_prefix(institution, default_prefix)
        return None

@receiver(post_save, sender=Invoice)
def create_invoice_journal_entry(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if instance.status != 'ISSUED':
        return

    # Check if entry already exists
    if JournalEntry.objects.filter(reference=f"Factura #{instance.number}", institution=instance.institution).exists():
        return

    # Use transaction for atomicity
    with transaction.atomic():
        # Create Header
        entry = JournalEntry.objects.create(
            institution=instance.institution,
            date=instance.issue_date,
            description=f"Factura de Venta - {instance.student.get_full_name()} ({instance.number})",
            reference=f"Factura #{instance.number}",
            state='POSTED',
            created_by=instance.created_by
        )

        # 1. DEBIT: Cuentas por Cobrar (Asset) - Total Amount
        # Key: ASSET_CXC. Fallback: 1.1.02.01 or 1.1.02
        cxc_account = get_configured_account(instance.institution, 'ASSET_CXC', '1.1.02.01')
        if not cxc_account:
             cxc_account = get_account_by_code_prefix(instance.institution, '1.1.02')

        JournalItem.objects.create(
            journal_entry=entry,
            account=cxc_account,
            description="Cuentas por Cobrar Clientes",
            debit=instance.total,
            credit=0
        )

        # 2. CREDIT: Ingresos / Ventas (Income) - Subtotal
        # Key: INCOME_SERVICES. Fallback: 4.1.02
        income_account = get_configured_account(instance.institution, 'INCOME_SERVICES', '4.1.02')
        
        JournalItem.objects.create(
            journal_entry=entry,
            account=income_account,
            description="Servicios Educativos",
            debit=0,
            credit=instance.subtotal_15 + instance.subtotal_0 # Total base
        )

        # 3. CREDIT: IVA (Liability) - If any
        if instance.iva_total > 0:
             # Key: LIABILITY_IVA. Fallback: 2.1
             iva_account = get_configured_account(instance.institution, 'LIABILITY_IVA', '2.1')
             
             JournalItem.objects.create(
                journal_entry=entry,
                account=iva_account,
                description="IVA Cobrado",
                debit=0,
                credit=instance.iva_total
            )

@receiver(post_save, sender=Payment)
def create_payment_journal_entry(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    """
    When a Payment is saved (indicating money received), we create a Journal Entry.
    Dr: Active (Cash/Bank)
    Cr: Receivable (Cuentas por Cobrar)
    """
    if not created:
         return
    
    invoice = instance.invoice
    institution = invoice.institution
    amount = instance.amount_paid
    
    # Check duplicate
    if JournalEntry.objects.filter(reference=f"Cobro Factura #{invoice.number}", institution=institution).exists():
        return

    with transaction.atomic():
        # Create Header
        entry = JournalEntry.objects.create(
            institution=institution,
            date=instance.payment_date.date(),
            description=f"Cobro de Factura - {invoice.student.get_full_name()} ({invoice.number})",
            reference=f"Cobro Factura #{invoice.number}",
            state='POSTED',
            created_by=invoice.created_by 
        )

        # 1. Determine ASSET Account (DEBIT)
        payment_method_name = invoice.payment_method.name.lower() if invoice.payment_method else ""
        
        if "efectivo" in payment_method_name:
            # Key: ASSET_CASH. Fallback: 1.1.01
            asset_account = get_configured_account(institution, 'ASSET_CASH', '1.1.01')
        else:
            # Key: ASSET_BANK. Fallback: 1.1.03
            asset_account = get_configured_account(institution, 'ASSET_BANK', '1.1.03')

        if not asset_account:
            asset_account = get_account_by_code_prefix(institution, '1.1') 

        JournalItem.objects.create(
            journal_entry=entry,
            account=asset_account,
            description=f"Cobro por {invoice.payment_method.name if invoice.payment_method else 'Desconocido'}",
            debit=amount,
            credit=0
        )

        # 2. Determine RECEIVABLE Account (CREDIT)
        # Key: ASSET_CXC. Fallback: 1.1.02.01
        receivable_account = get_configured_account(institution, 'ASSET_CXC', '1.1.02.01')
        if not receivable_account:
             receivable_account = get_account_by_code_prefix(institution, '1.1.02')
        
        JournalItem.objects.create(
            journal_entry=entry,
            account=receivable_account,
            description="Cierre de CxC",
            debit=0,
            credit=amount
        )
