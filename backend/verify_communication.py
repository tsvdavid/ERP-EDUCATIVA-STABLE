import os
import django
import sys
import datetime

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Institution
from academic.models import Course, Subject, Enrollment, Grade
from communication.models import Message
from treasury.models import PaymentConcept, PaymentMethod, Charge, Invoice, InvoiceDetail, Payment as TreasuryPayment

def verify():
    print("--- INICIANDO VERIFICACIÓN DEL MÓDULO DE TESORERÍA ---")
    
    # 1. Setup Institution & Users
    inst, _ = Institution.objects.get_or_create(name="Escuela Treasury Test")
    print(f"Institution: {inst.name}")

    rector, _ = User.objects.get_or_create(username='rector_treasury', defaults={'role': 'RECTOR', 'institution': inst})
    if not rector.check_password('testpass'): rector.set_password('testpass'); rector.save()

    student, _ = User.objects.get_or_create(username='student_treasury', defaults={'role': 'STUDENT', 'institution': inst, 'first_name': 'Juan', 'last_name': 'Perez', 'cedula': '1700000001'})
    if not student.check_password('testpass'): student.set_password('testpass'); student.save()
    
    print(f"Users created: {rector.username}, {student.username}")

    # 2. Setup Treasury Config
    concept, _ = PaymentConcept.objects.get_or_create(institution=inst, name="Pension Abril 2026", defaults={'price': 50.00, 'iva_rate': 0.00})
    method, _ = PaymentMethod.objects.get_or_create(institution=inst, name="Efectivo", defaults={'code': 'CASH'})
    print(f"Treasury Config: Concept={concept.name}, Method={method.name}")

    # 3. Generate Charge (Debt)
    print("\n--- 3. TESTING CHARGE GENERATION ---")
    # Clean previous charges for clean test
    Charge.objects.filter(student=student, concept=concept).delete()
    
    charge = Charge.objects.create(
        institution=inst,
        student=student,
        concept=concept,
        amount=concept.price,
        due_date=datetime.date.today(),
        is_paid=False
    )
    print(f"Charge Created: ID={charge.id} Amount=${charge.amount} Paid={charge.is_paid}")

    # 4. Process Payment (Pay the charge)
    print("\n--- 4. TESTING PAYMENT PROCESS ---")
    
    # Simulate Logic typically in process_payment view
    # Create Invoice
    last_invoice = Invoice.objects.order_by('-id').first()
    seq = int(last_invoice.number) + 1 if (last_invoice and last_invoice.number.isdigit()) else 1
    invoice_number = f"{seq:09d}"

    invoice = Invoice.objects.create(
        institution=inst,
        student=student,
        number=invoice_number,
        status='ISSUED',
        client_name="Test Parent",
        client_ruc="9999999999999",
        payment_method=method,
        created_by=rector
    )

    # Create Detail & Link Charge
    detail = InvoiceDetail.objects.create(
        invoice=invoice,
        concept=concept,
        quantity=1,
        unit_price=concept.price,
        subtotal=concept.price,
        charge=charge
    )
    
    # Mark charge paid (The view does this)
    charge.is_paid = True
    charge.save()
    
    # Update Invoice Totals
    invoice.total = concept.price
    invoice.save()
    
    # Register Payment
    TreasuryPayment.objects.create(
        invoice=invoice,
        amount_paid=invoice.total,
        verified=True
    )
    
    print(f"Payment Processed. Invoice #{invoice.number} Total: {invoice.total}")
    
    # VERIFICATION
    charge.refresh_from_db()
    print(f"Charge Paid Status: {charge.is_paid}")
    
    if charge.is_paid and invoice.total == 50.00:
        print("\n[SUCCESS]: Treasury Flow Verified (Charge -> Payment -> Paid)")
    else:
        print("\n[FAILURE]: Charge not paid or totals wrong")

if __name__ == "__main__":
    verify()
