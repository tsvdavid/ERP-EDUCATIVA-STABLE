import os
import django
import sys
import threading
import time
from decimal import Decimal

# Setup Django environment
sys.path.append('/var/www/erpeducativa/ERP-EDUCATIVA/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from users.models import User, Institution
from treasury.models import Customer, PaymentMethod, PaymentConcept

def create_invoice_worker(inst_id, user, customer_id, pm_id, concept_id, index, results):
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Header for middleware
    headers = {'HTTP_X_INSTITUTION_ID': str(inst_id)}
    
    payload = {
        "customer_id": customer_id,
        "payment_method_id": pm_id,
        "client_name": "Stress Test Client",
        "client_ruc": "1799999999001",
        "client_address": "Test Address",
        "client_email": "test@example.com",
        "concepts": [
            {
                "concept_id": concept_id,
                "quantity": 1
            }
        ]
    }
    
    start_time = time.time()
    try:
        response = client.post('/api/treasury/invoices/process-payment/', payload, format='json', **headers)
        results.append((response.status_code, time.time() - start_time, response.data if response.status_code not in [200, 201] else None))
    except Exception as e:
        results.append(('ERROR', time.time() - start_time, str(e)))

def run_stress_test():
    print("--- INICIANDO TEST DE ESTRÉS REAL (ENDPOINT: process-payment) ---\n")
    print("Concurrencia: 50 | Prefijo: [FRONTEND SIMULATION]")
    
    inst_id = 18
    user = User.objects.filter(institution_id=inst_id).first()
    customer = Customer.objects.filter(institution_id=inst_id).first()
    pm = PaymentMethod.objects.filter(institution_id=inst_id).first()
    concept = PaymentConcept.objects.filter(institution_id=inst_id).first()
    
    if not all([user, customer, pm, concept]):
        print(f"Error: Datos insuficientes en Inst {inst_id}")
        return

    threads = []
    results = []
    
    for i in range(50):
        t = threading.Thread(target=create_invoice_worker, args=(inst_id, user, customer.id, pm.id, concept.id, i, results))
        threads.append(t)
    
    start_all = time.time()
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    end_all = time.time()
    
    successes = [r for r in results if r[0] in [200, 201]]
    errors = [r for r in results if r[0] not in [200, 201]]
    
    print(f"\nResultados Finales:")
    print(f"  - Éxitos (HTTP OK): {len(successes)}")
    print(f"  - Fallos: {len(errors)}")
    print(f"  - Tiempo total de ejecución: {end_all - start_all:.2f}s")
    
    if successes:
        avg_time = sum(s[1] for s in successes) / len(successes)
        print(f"  - Latencia promedio por petición: {avg_time:.4f}s")
    
    if errors:
        print("\nDetalle de los primeros fallos detectados:")
        for e in errors[:5]:
            print(f"    - Status: {e[0]}, Error: {e[2]}")

    print("\n--- TEST DE ESTRÉS COMPLETADO ---")

if __name__ == "__main__":
    run_stress_test()
