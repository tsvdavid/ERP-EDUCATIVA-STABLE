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

from treasury.models import Invoice, InvoiceDetail, Customer
from users.models import Institution, User

def create_invoice_worker(institution_id, customer_id, client_name, client_ruc, user_id, index, results):
    from django.db import connection, transaction
    
    start_time = time.time()
    try:
        with transaction.atomic():
            # Manual tenant context for DB session in thread
            with connection.cursor() as cursor:
                cursor.execute(f"SET app.current_tenant = {institution_id}")
            
            invoice = Invoice.objects.create(
                institution_id=institution_id,
                customer_id=customer_id,
                client_name=client_name,
                client_ruc=client_ruc,
                number=f"S-{int(time.time())}-{index}",
                status='DRAFT',
                total=Decimal('100.00'),
                created_by_id=user_id
            )
            InvoiceDetail.objects.create(
                institution_id=institution_id,
                invoice=invoice,
                description="Stress Test Item",
                quantity=1,
                unit_price=Decimal('100.00'),
                total_price=Decimal('100.00')
            )
            # Emitir para activar señales contables
            invoice.status = 'ISSUED'
            invoice.save()
            
        results.append(('SUCCESS', time.time() - start_time))
    except Exception as e:
        results.append(('FAILURE', str(e)))

def run_stress_test():
    print("--- INICIANDO TEST DE ESTRÉS: 50 CREACIONES CONCURRENTES ---\n")
    
    inst_id = 18 # Valencia Puente (Prod-like)
    customer = Customer.objects.filter(institution_id=inst_id).first()
    user = User.objects.filter(institution_id=inst_id).first()
    
    if not customer or not user:
        print(f"Error: No se encontró cliente o usuario para el test en Inst {inst_id}")
        return

    threads = []
    results = []
    
    for i in range(50):
        t = threading.Thread(target=create_invoice_worker, args=(inst_id, customer.id, customer.first_name, customer.identification, user.id, i, results))
        threads.append(t)
    
    start_all = time.time()
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    end_all = time.time()
    
    successes = [r for r in results if r[0] == 'SUCCESS']
    failures = [r for r in results if r[0] == 'FAILURE']
    
    print(f"Resultados:")
    print(f"  - Éxitos: {len(successes)}")
    print(f"  - Fallos: {len(failures)}")
    print(f"  - Tiempo total: {end_all - start_all:.2f}s")
    
    if failures:
        print("\nPrimeros 5 fallos:")
        for f in failures[:5]:
            print(f"    - {f[1]}")
    
    if successes:
        avg_time = sum(s[1] for s in successes) / len(successes)
        print(f"  - Tiempo promedio por creación: {avg_time:.4f}s")

    print("\n--- TEST DE ESTRÉS COMPLETADO ---")

if __name__ == "__main__":
    run_stress_test()
