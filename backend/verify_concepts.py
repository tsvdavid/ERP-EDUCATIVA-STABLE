import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import PaymentConcept
from users.models import Institution

try:
    print("Testing PaymentConcept retrieval...")
    concepts = PaymentConcept.objects.filter(is_active=True)
    print(f"Found {concepts.count()} active concepts.")
    for c in concepts:
        print(f" - {c.name} (${c.price})")
    
    # Check if any institution is missing?
    invalid = PaymentConcept.objects.filter(institution__isnull=True)
    if invalid.exists():
        print(f"WARNING: Found {invalid.count()} concepts without institution!")

except Exception as e:
    print(f"FAILED: {e}")
