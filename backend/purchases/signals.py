from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import PurchaseInvoice
from accounting.models import JournalEntry, JournalItem, AccountingConfig
from accounting.signals import get_configured_account, get_account_by_code_prefix

@receiver(post_save, sender=PurchaseInvoice)
def create_purchase_journal_entry(sender, instance, created, **kwargs):
    """
    Generates Journal Entry for Validated Purchases.
    Dr: Expense (Gasto) - From items
    Dr: Tax Credit (IVA Compras)
    Cr: Payable (Proveedores)
    """
    if instance.status != 'VALIDATED':
        return

    # Check duplicate
    if JournalEntry.objects.filter(reference=f"Compra #{instance.document_number}", institution=instance.institution).exists():
        return

    with transaction.atomic():
        entry = JournalEntry.objects.create(
            institution=instance.institution,
            date=instance.issue_date,
            description=f"Compra a {instance.supplier.legal_name} - Factura {instance.document_number}",
            reference=f"Compra #{instance.document_number}",
            state='POSTED',
            created_by=instance.created_by
        )

        # 1. EXPENSES (Dr)
        total_expense = 0
        for item in instance.items.all():
            expense_acc = item.expense_account
            # If no specific account, try to find a generic one? For now assume it's mandatory or handle null
            if not expense_acc:
                # Fallback to generic Expense? Not ideal.
                continue
            
            JournalItem.objects.create(
                journal_entry=entry,
                account=expense_acc,
                description=item.description,
                debit=item.subtotal,
                credit=0
            )
            total_expense += item.subtotal

        # 2. TAX CREDIT (Dr) - IVA
        if instance.iva > 0:
            tax_account = get_configured_account(instance.institution, 'ASSET_TAX_CREDIT', '1.1.05') # Placeholder fallback
            if not tax_account:
                 # Try 1.1 active
                 tax_account = get_account_by_code_prefix(instance.institution, '1.1')

            JournalItem.objects.create(
                journal_entry=entry,
                account=tax_account,
                description="IVA en Compras (Crédito Tributario)",
                debit=instance.iva,
                credit=0
            )

        # 3. PAYABLE (Cr) - Suppliers
        payable_account = get_configured_account(instance.institution, 'LIABILITY_SUPPLIERS', '2.1.03') # Placeholder
        if not payable_account:
             payable_account = get_account_by_code_prefix(instance.institution, '2.1')

        JournalItem.objects.create(
            journal_entry=entry,
            account=payable_account,
            description=f"CxP Proveedor {instance.supplier.legal_name}",
            debit=0,
            credit=instance.total
        )
