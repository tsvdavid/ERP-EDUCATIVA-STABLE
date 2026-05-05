import os
import django
import threading
import time
import random
import traceback
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import Invoice, InvoiceSequence, Customer, PaymentConcept, PaymentMethod
from treasury.utils import get_next_invoice_number
from users.models import Institution, User
from django.db import transaction, connection

def stress_test_concurrency(institution_id, count=50):
    inst = Institution.objects.get(id=institution_id)
    results = []
    errors = []
    
    # We will use a real user as issuer
    user = User.objects.filter(institution=inst, role='ADMIN').first()
    if not user:
        # Create a dummy user for testing
        user, _ = User.objects.get_or_create(username='test_issuer', institution=inst, defaults={'role': 'ADMIN', 'is_staff': True})

    # Prepare student
    student = User.objects.filter(institution=inst, role='STUDENT').first()
    if not student:
        student, _ = User.objects.get_or_create(
            username='test_student', 
            institution=inst, 
            defaults={'role': 'STUDENT', 'first_name': 'TEST', 'last_name': 'STUDENT'}
        )

    # Prepare customer
    customer, _ = Customer.objects.get_or_create(
        identification='9999999999',
        institution=inst,
        defaults={
            'student': student,
            'first_name': 'STRESS', 
            'last_name': 'TEST', 
            'email': 'test@example.com', 
            'address': 'Testing Lane'
        }
    )
    
    start_time = time.time()
    
    def create_invoice_task(thread_id):
        try:
            # Re-establish connection per thread to avoid shared cursor issues in some setups
            connection.close() 
            
            # Use the utility to get a number and create
            with transaction.atomic():
                number = get_next_invoice_number(inst, '001', '001')
                Invoice.objects.create(
                    institution=inst,
                    customer=customer,
                    student=student,
                    number=number,
                    status='ISSUED',
                    client_name='STRESS TEST',
                    client_ruc='9999999999',
                    created_by=user,
                    total=Decimal('10.00')
                )
                results.append(number)
        except Exception as e:
            traceback.print_exc()
            errors.append(f"Thread {thread_id}: {str(e)}")

    threads = []
    for i in range(count):
        t = threading.Thread(target=create_invoice_task, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    end_time = time.time()
    duration = end_time - start_time

    # --- VERIFICATION ---
    print(f"\n--- AUDIT REPORT: INVOICING CONCURRENCY ---")
    print(f"Goal: {count} simultaneous invoices")
    print(f"Successful: {len(results)}")
    print(f"Errors: {len(errors)}")
    if errors:
        for err in errors[:5]:
            print(f"  - {err}")

    # Check for duplicates
    unique_results = set(results)
    duplicates = len(results) - len(unique_results)
    print(f"Duplicates detected: {duplicates}")

    # Check sequence
    results.sort()
    is_consecutive = True
    if results:
        # Extract seq parts
        seqs = [int(r.split('-')[2]) for r in results]
        for i in range(1, len(seqs)):
            if seqs[i] != seqs[i-1] + 1:
                is_consecutive = False
                print(f"  Gap detected: {seqs[i-1]} -> {seqs[i]}")
    
    print(f"Sequence is consecutive: {is_consecutive}")
    print(f"Total duration: {duration:.2f}s ({duration/count*1000:.1f}ms per invoice)")

def test_rollback(institution_id):
    print(f"\n--- AUDIT REPORT: ROLLBACK VALIDATION ---")
    inst = Institution.objects.get(id=institution_id)
    
    # Get current sequence
    seq_obj = InvoiceSequence.objects.filter(institution=inst, establishment='001', emission_point='001').first()
    initial_seq = seq_obj.next_number if seq_obj else 1
    print(f"Initial sequence: {initial_seq}")

    try:
        with transaction.atomic():
            number = get_next_invoice_number(inst, '001', '001')
            print(f"Obtained number: {number} (Expect {initial_seq:09d})")
            raise Exception("Simulated failure to trigger rollback")
    except Exception as e:
        print(f"Exception caught: {str(e)}")

    # Check if sequence was rolled back
    # IMPORTANT: In some DBs like Postgres, sequences DON'T rollback if they are native sequences.
    # BUT we are using a table and 'select_for_update', so it MUST rollback.
    seq_obj_after = InvoiceSequence.objects.filter(institution=inst, establishment='001', emission_point='001').first()
    final_seq = seq_obj_after.next_number if seq_obj_after else 1
    
    print(f"Final sequence after rollback: {final_seq}")
    if initial_seq == final_seq:
        print("Rollback successful: No gaps generated.")
    else:
        print("Rollback FAILED: Gap generated (This happens if not using table locks correctly).")

if __name__ == "__main__":
    # Use institution 1 for testing (usually 'Netforce' or similar)
    test_inst_id = 1
    stress_test_concurrency(test_inst_id, 50)
    test_rollback(test_inst_id)
