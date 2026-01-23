import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Institution, User
from purchases.models import Supplier, PurchaseInvoice, PurchaseItem
from accounting.models import JournalEntry, JournalItem, Account, AccountingConfig

def verify_purchases():
    print("--- Verifying Purchases Module ---")

    # 1. Setup Data
    institution = Institution.objects.first()
    if not institution:
        print("ERROR: No institution found.")
        return
    
    admin_user = User.objects.filter(institution=institution).first()
    if not admin_user:
        print("ERROR: No user found.")
        return

    print(f"Using Institution: {institution.name}")

    # 2. Create Supplier
    supplier, created = Supplier.objects.get_or_create(
        institution=institution,
        tax_id="0999999999001",
        defaults={
            'legal_name': "PROVEEDOR DE PRUEBA S.A.",
            'email': "proveedor@test.com",
            'address': "Av. Test 123"
        }
    )
    print(f"Supplier: {supplier.legal_name} {'(Created)' if created else '(Found)'}")

    # 3. Create Purchase Invoice
    invoice = PurchaseInvoice.objects.create(
        institution=institution,
        supplier=supplier,
        document_number="001-001-TEST001",
        issue_date="2024-01-15",
        status='DRAFT',
        created_by=admin_user,
        subtotal_15=Decimal("100.00"),
        iva=Decimal("15.00"),
        total=Decimal("115.00")
    )
    print(f"Created Draft Invoice: {invoice.document_number}")

    # 4. Create Items
    # Need an expense account. Try to find one or create generic.
    expense_acc = Account.objects.filter(institution=institution, account_type='EXPENSE').first()
    if not expense_acc:
        # Create dummy expense account
        expense_acc = Account.objects.create(
            institution=institution,
            code="5.1.99",
            name="Gasto de Prueba",
            account_type='EXPENSE'
        )
    
    PurchaseItem.objects.create(
        invoice=invoice,
        description="Material de Oficina",
        quantity=1,
        unit_price=100.00,
        subtotal=100.00,
        tax_rate=15,
        expense_account=expense_acc
    )
    print("Added Purchase Item.")

    # 5. Validate Invoice (Trigger Signal)
    print("Validating Invoice...")
    invoice.status = 'VALIDATED'
    invoice.save()

    # 6. Verify Accounting
    entry = JournalEntry.objects.filter(reference=f"Compra #{invoice.document_number}", institution=institution).first()
    if entry:
        print(f"SUCCESS: Journal Entry Created! ID: {entry.id}")
        print(f"Description: {entry.description}")
        print("Items:")
        for item in entry.items.all():
            print(f" - {item.account.code} ({item.account.name}): D:{item.debit} C:{item.credit}")
            
        if entry.is_balanced:
             print(" - Entry is BALANCED.")
        else:
             print(" - Entry is UNBALANCED!")
    else:
        print("FAILURE: No Journal Entry found.")

    # Cleanup (Optional)
    # invoice.delete()
    # supplier.delete()

if __name__ == "__main__":
    verify_purchases()
