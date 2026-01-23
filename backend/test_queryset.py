import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from purchases.models import PurchaseInvoice

try:
    print("Testing select_related('withholding')...")
    qs = PurchaseInvoice.objects.all().select_related('withholding')
    print(f"Query: {qs.query}")
    print("Fetching first items...")
    for i in qs[:5]:
        print(f"Invoice: {i}, Withholding: {getattr(i, 'withholding', 'None')}")
    print("Success!")
except Exception as e:
    print(f"FAILED: {e}")
