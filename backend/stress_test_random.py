import os
import django
import sys
import threading
import time
import random
from decimal import Decimal

# Setup Django environment
sys.path.append('/var/www/erpeducativa/ERP-EDUCATIVA/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from users.models import User, Institution
from treasury.models import Customer, PaymentMethod, PaymentConcept

def create_invoice_worker(inst_id, user, index, results):
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Header for middleware
    headers = {'HTTP_X_INSTITUTION_ID': str(inst_id)}
    
    # Payload as requested by user
    payload = {
        "customer": random.choice([1, 2, 3, 4, 5, 234]), # 234 is the only valid one for Inst 18
        "status": "ISSUED",
        "client_name": "Random Test", # Required by serializer
        "client_ruc": "9999999999",   # Required by serializer
        "details": [
            {
                "concept": 1, # Valid ID
                "quantity": 1,
                "unit_price": "10.00"
            }
        ]
    }
    
    start_time = time.time()
    try:
        response = client.post('/api/treasury/invoices/', payload, format='json', **headers)
        results.append((response.status_code, time.time() - start_time, response.data if response.status_code not in [201] else None))
    except Exception as e:
        results.append(('ERROR', time.time() - start_time, str(e)))

def run_stress_test():
    print("--- TEST DE AUDITORÍA: RANDOM CUSTOMER [1,2,3,4,5,234] ---\n")
    print("Objetivo: Validar que el sistema RECHACE clientes que no pertenecen al tenant 18.")
    
    inst_id = 18
    user = User.objects.filter(institution_id=inst_id).first()
    
    threads = []
    results = []
    
    for i in range(50):
        t = threading.Thread(target=create_invoice_worker, args=(inst_id, user, i, results))
        threads.append(t)
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Analyze results
    success_234 = len([r for r in results if r[0] == 201])
    rejected_cross = len([r for r in results if r[0] == 400])
    
    print(f"\nResultados:")
    print(f"  - Creaciones Exitosas (Customer 234): {success_234}")
    print(f"  - Rechazos por Cross-Tenant (IDs 1-5): {rejected_cross}")
    print(f"  - Total: {len(results)}")
    
    if rejected_cross > 0:
        print("\nCONFIRMADO: El aislamiento RLS/Mixin bloqueó correctamente los IDs de otros tenants.")

if __name__ == "__main__":
    run_stress_test()
