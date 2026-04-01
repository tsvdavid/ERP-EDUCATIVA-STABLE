import os
import django
import sys
from django.db import transaction

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Institution, User
from accounting.models import Account, FiscalYear, JournalEntry, JournalItem, AccountingConfig

def copy_accounting_data(source_name, target_name):
    print(f"=== COPYING ACCOUNTING DATA: {source_name} -> {target_name} ===")

    try:
        source_inst = Institution.objects.get(name=source_name)
        target_inst = Institution.objects.get(name=target_name)
    except Institution.DoesNotExist as e:
        print(f"Error: Institution not found: {e}")
        return

    print(f"Source ID: {source_inst.id}")
    print(f"Target ID: {target_inst.id}")

    # clean target (optional, but safer for "copy all" request)
    # print("Cleaning target accounting data...")
    # JournalItem.objects.filter(journal_entry__institution=target_inst).delete()
    # JournalEntry.objects.filter(institution=target_inst).delete()
    # AccountingConfig.objects.filter(institution=target_inst).delete()
    # Account.objects.filter(institution=target_inst).delete()
    # FiscalYear.objects.filter(institution=target_inst).delete()
    
    # 1. Fiscal Years
    print("1. Copying Fiscal Years...")
    fy_map = {} # old_id -> new_instance
    for fy in FiscalYear.objects.filter(institution=source_inst):
        new_fy, created = FiscalYear.objects.get_or_create(
            institution=target_inst,
            year=fy.year,
            defaults={'is_closed': fy.is_closed}
        )
        if created:
            print(f"   Created Fiscal Year: {new_fy.year}")
        else:
            print(f"   Fiscal Year {new_fy.year} already exists.")

    # 2. Accounts (Ordered by level to ensure parents exist)
    print("2. Copying Accounts...")
    account_map = {} # old_id -> new_instance
    
    # Get all source accounts, ordered by level and code
    source_accounts = Account.objects.filter(institution=source_inst).order_by('level', 'code')
    
    with transaction.atomic():
        for acc in source_accounts:
            # Find parent if exists
            new_parent = None
            if acc.parent:
                if acc.parent.id in account_map:
                    new_parent = account_map[acc.parent.id]
                else:
                    print(f"   [WARNING] Parent {acc.parent.code} not found yet for {acc.code}. Skipping hierarchy.")
            
            # Create or Get Account
            new_acc, created = Account.objects.get_or_create(
                institution=target_inst,
                code=acc.code,
                defaults={
                    'name': acc.name,
                    'account_type': acc.account_type,
                    'parent': new_parent,
                    'level': acc.level,
                    'is_active': acc.is_active,
                    'description': acc.description,
                    'tax_id': acc.tax_id
                }
            )
            
            # If it already existed but verify parent
            if not created and new_acc.parent != new_parent:
                new_acc.parent = new_parent
                new_acc.save()
                
            account_map[acc.id] = new_acc
            # print(f"   Mapped {acc.code}")

    print(f"   Copied {len(account_map)} accounts.")

    # 3. Journal Entries and Items
    print("3. Copying Journal Entries...")
    entries_count: int = 0
    items_count: int = 0
    
    source_entries = JournalEntry.objects.filter(institution=source_inst)
    
    # Needs a user for created_by
    # Try to find a user in target inst, or use the first admin found
    admin_user = User.objects.filter(institution=target_inst, role='ADMIN').first()
    if not admin_user:
         admin_user = User.objects.filter(is_superuser=True).first()
    
    if not admin_user:
        print("   [ERROR] No user found to assign entries. Aborting Journal Copy.")
        return

    with transaction.atomic():
        for entry in source_entries:
            # Check if duplicate (by reference and date? strictly speaking, we want a copy, so maybe duplications are allowed or filtered)
            # Let's filter by reference to avoid running script twice and duplicating
            if JournalEntry.objects.filter(institution=target_inst, reference=entry.reference, date=entry.date).exists():
                # print(f"   Skipping existing entry: {entry.reference}")
                continue

            new_entry = JournalEntry.objects.create(
                institution=target_inst,
                date=entry.date,
                description=entry.description,
                reference=entry.reference,
                state=entry.state,
                created_by=admin_user, # Assign to valid user
                # posted_at logic if needed
            )
            
            entries_count += 1
            
            # Copy Items
            for item in entry.items.all():
                if item.account.id in account_map:
                    JournalItem.objects.create(
                        journal_entry=new_entry,
                        account=account_map[item.account.id],
                        description=item.description,
                        debit=item.debit,
                        credit=item.credit
                    )
                    items_count += 1
                else:
                    print(f"   [ERROR] Account ID {item.account.id} ({item.account.code}) not found in map. Skipping item.")

    print(f"   Copied {entries_count} entries with {items_count} items.")
    
    # 4. Accounting Config
    print("4. Copying Accounting Configurations...")
    
    source_configs = AccountingConfig.objects.filter(institution=source_inst)
    for conf in source_configs:
        if conf.account.id in account_map:
            AccountingConfig.objects.get_or_create(
                institution=target_inst,
                key=conf.key,
                defaults={'account': account_map[conf.account.id]}
            )
        else:
             print(f"   [WARNING] Config account {conf.account.code} not found for key {conf.key}")
             
    print("=== DONE ===")

if __name__ == '__main__':
    # Source -> Target
    copy_accounting_data("Unidad Educativa GitHub Copilot", "Unidad Educativa Prisca")
