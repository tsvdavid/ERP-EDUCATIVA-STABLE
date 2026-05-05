from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from treasury.models import Invoice, Payment, CreditNote
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
        # If not ISSUED, we still check for cancellation to reverse accounting
        if instance.status == 'CANCELLED':
            entry = JournalEntry.objects.filter(
                reference=f"Factura #{instance.number}", 
                institution=instance.institution
            ).first()
            if entry and entry.state != 'CANCELLED':
                entry.state = 'CANCELLED'
                entry.save()
        return

    # Check if entry already exists
    if JournalEntry.objects.filter(reference=f"Factura #{instance.number}", institution=instance.institution).exists():
        return

    # Use transaction for atomicity
    with transaction.atomic():
        # Create Header
        student_name = instance.student.get_full_name() if instance.student else instance.client_name
        entry = JournalEntry.objects.create(
            institution=instance.institution,
            date=instance.issue_date,
            description=f"Factura de Venta - {student_name} ({instance.number})",
            reference=f"Factura #{instance.number}",
            state='POSTED',
            created_by=instance.created_by
        )

        # 1. DEBIT: Cuentas por Cobrar (Asset) - Total Amount
        cxc_account = get_configured_account(instance.institution, 'ASSET_CXC', '1.1.02.01')
        if not cxc_account:
             cxc_account = get_account_by_code_prefix(instance.institution, '1.1.02')
        
        if not cxc_account:
            raise Exception(f"Error Contable: No se encontró la cuenta de Cuentas por Cobrar (ASSET_CXC) para la institución {instance.institution_id}")

        JournalItem.objects.create(
            institution=instance.institution,
            journal_entry=entry,
            account=cxc_account,
            description="Cuentas por Cobrar Clientes",
            debit=instance.total,
            credit=0
        )

        # 2. CREDIT: Ingresos / Ventas (Income) - Subtotal
        income_account = get_configured_account(instance.institution, 'INCOME_SERVICES', '4.1.02')
        if not income_account:
            raise Exception(f"Error Contable: No se encontró la cuenta de Ingresos (INCOME_SERVICES) para la institución {instance.institution_id}")
        
        JournalItem.objects.create(
            institution=instance.institution,
            journal_entry=entry,
            account=income_account,
            description="Servicios Educativos",
            debit=0,
            credit=instance.subtotal_15 + instance.subtotal_0
        )

        # 3. CREDIT: IVA (Liability) - If any
        if instance.iva_total > 0:
             iva_account = get_configured_account(instance.institution, 'LIABILITY_IVA', '2.1')
             if not iva_account:
                raise Exception(f"Error Contable: No se encontró la cuenta de IVA (LIABILITY_IVA) para la institución {instance.institution_id}")
             
             JournalItem.objects.create(
                institution=instance.institution,
                journal_entry=entry,
                account=iva_account,
                description="IVA Cobrado",
                debit=0,
                credit=instance.iva_total
            )

        # 4. DEBIT: Descuentos (Expense) - If any
        if instance.discount > 0:
             discount_account = get_configured_account(instance.institution, 'EXPENSE_DISCOUNTS', '5.1')
             if not discount_account:
                 # Non-critical if missing? No, let's be strict
                 pass 
             
             if discount_account:
                 JournalItem.objects.create(
                    institution=instance.institution,
                    journal_entry=entry,
                    account=discount_account,
                    description="Descuentos Concedidos",
                    debit=instance.discount,
                    credit=0
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
        student_name = invoice.student.get_full_name() if invoice.student else invoice.client_name
        entry = JournalEntry.objects.create(
            institution=institution,
            date=instance.payment_date.date(),
            description=f"Cobro de Factura - {student_name} ({invoice.number})",
            reference=f"Cobro Factura #{invoice.number}",
            state='POSTED',
            created_by=invoice.created_by 
        )

        # 1. Determine ASSET Account (DEBIT)
        payment_method_name = invoice.payment_method.name.lower() if invoice.payment_method else ""
        
        if "efectivo" in payment_method_name:
            asset_account = get_configured_account(institution, 'ASSET_CASH', '1.1.01')
        else:
            asset_account = get_configured_account(institution, 'ASSET_BANK', '1.1.03')

        if not asset_account:
            asset_account = get_account_by_code_prefix(institution, '1.1') 

        JournalItem.objects.create(
            institution=institution,
            journal_entry=entry,
            account=asset_account,
            description=f"Cobro por {invoice.payment_method.name if invoice.payment_method else 'Desconocido'}",
            debit=amount,
            credit=0
        )

        # 2. Determine RECEIVABLE Account (CREDIT)
        receivable_account = get_configured_account(institution, 'ASSET_CXC', '1.1.02.01')
        if not receivable_account:
             receivable_account = get_account_by_code_prefix(institution, '1.1.02')
        
        JournalItem.objects.create(
            institution=institution,
            journal_entry=entry,
            account=receivable_account,
            description="Cierre de CxC",
            debit=0,
            credit=amount
        )

@receiver(post_save, sender=CreditNote)
def create_credit_note_journal_entry(sender, instance, created, **kwargs):
    if not created or instance.status != 'ISSUED':
        return

    # A Credit Note reverses an Invoice:
    # Dr: Income (Service)
    # Dr: Liability (IVA)
    # Cr: Asset (CxC)
    
    with transaction.atomic():
        entry = JournalEntry.objects.create(
            institution=instance.institution,
            date=instance.issue_date,
            description=f"Nota de Crédito - {instance.invoice.number}",
            reference=f"NC #{instance.number}",
            state='POSTED',
            created_by=instance.created_by
        )

        # 1. DEBIT: Ingresos (Reversal)
        income_account = get_configured_account(instance.institution, 'INCOME_SERVICES', '4.1.02')
        JournalItem.objects.create(
            institution=instance.institution,
            journal_entry=entry,
            account=income_account,
            description=f"Reverso Ingreso NC {instance.number}",
            debit=instance.total - instance.iva_total,
            credit=0
        )

        # 2. DEBIT: IVA (Reversal)
        if instance.iva_total > 0:
            iva_account = get_configured_account(instance.institution, 'LIABILITY_IVA', '2.1')
            JournalItem.objects.create(
                institution=instance.institution,
                journal_entry=entry,
                account=iva_account,
                description=f"Reverso IVA NC {instance.number}",
                debit=instance.iva_total,
                credit=0
            )

        # 3. CREDIT: CxC (Reversal)
        cxc_account = get_configured_account(instance.institution, 'ASSET_CXC', '1.1.02.01')
        JournalItem.objects.create(
            institution=instance.institution,
            journal_entry=entry,
            account=cxc_account,
            description=f"Reverso CxC NC {instance.number}",
            debit=0,
            credit=instance.total
        )
