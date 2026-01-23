import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import PaymentMethod
from users.models import Institution

def populate():
    # Ensure we have at least one institution
    inst = Institution.objects.first()
    if not inst:
        print("No institution found. Please create one first.")
        return

    methods = ['Efectivo', 'Transferencia Bancaria', 'Tarjeta de Crédito/Débito', 'Cheque']
    
    for name in methods:
        obj, created = PaymentMethod.objects.get_or_create(
            name=name,
            defaults={
                'institution': inst,
                'code': name[:3].upper()
            }
        )
        if created:
            print(f"Created: {name}")
        else:
            print(f"Exists: {name}")

if __name__ == '__main__':
    populate()
