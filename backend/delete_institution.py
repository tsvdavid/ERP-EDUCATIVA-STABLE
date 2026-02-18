import os
import django
import sys
from django.db import transaction

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Institution

def delete_institution(name):
    print(f"=== DELETING INSTITUTION: {name} ===")
    
    try:
        inst = Institution.objects.get(name=name)
    except Institution.DoesNotExist:
        print(f"Institution '{name}' not found.")
        return

    # Confirmation bypassed by user request in chat
    # confirm = input(f"Are you sure...? (yes/no): ")
    # if confirm.lower() != 'yes': return
    print("Confirmation received (via Agent). Proceeding...")

    count_users = inst.users.count()
    print(f"Deleting Institution with {count_users} users...")
    
    inst.delete()
    print("=== DELETION COMPLETE ===")

if __name__ == '__main__':
    # Hardcoded for safety based on request, or use arg
    delete_institution("Unidad Educativa GitHub Copilot")
