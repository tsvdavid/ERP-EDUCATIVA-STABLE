import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Institution

print("=== INSTITUTIONS ===")
for inst in Institution.objects.all():
    print(f"ID: {inst.id} | Name: '{inst.name}'")
