
import os
import django
import sys

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import PaymentMethod
from users.models import Institution

def populate():
    print("Standardizing SRI Payment Methods...")
    
    # SRI Codes
    # 01 - Efectivo -> SIN UTILIZACION DEL SISTEMA FINANCIERO
    # 19 - Tarjeta -> TARJETA DE CREDITO
    # 20 - Transferencia -> OTROS CON UTILIZACION DEL SISTEMA FINANCIERO
    
    methods = [
        {'code': '01', 'name': 'Efectivo'},
        {'code': '20', 'name': 'Transferencia Bancaria'},
        {'code': '19', 'name': 'Tarjeta de Crédito'},
    ]
    
    institutions = Institution.objects.all()
    
    if not institutions.exists():
        print("No institutions found.")
        return

    for inst in institutions:
        print(f"Processing for {inst.name}...")
        for m in methods:
            obj, created = PaymentMethod.objects.get_or_create(
                code=m['code'],
                institution=inst,
                defaults={'name': m['name'], 'is_active': True}
            )
            if created:
                print(f"  Created {m['name']} ({m['code']})")
            else:
                print(f"  Existing {m['name']} ({m['code']})")
                obj.name = m['name'] # Ensure name is updated if code matches
                obj.save()

    print("Done.")

if __name__ == '__main__':
    populate()
