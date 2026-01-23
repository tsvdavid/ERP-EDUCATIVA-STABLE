
import os
import sys
import django
import random
from decimal import Decimal
from datetime import date, timedelta, datetime

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from users.models import User, Institution
from academic.models import AcademicYear, AcademicPeriod, Course, Subject, Enrollment, Grade, EvaluationCategory
from treasury.models import PaymentConcept, PaymentMethod, Charge, Invoice, Payment, InvoiceDetail
from communication.models import Notice, Message
from helpdesk.models import ServiceCatalog, Ticket, PassStep, Workflow
from purchases.models import Supplier, PurchaseInvoice, PurchaseItem
from accounting.models import Account, AccountingConfig

def populate():
    print(">>> DATO POPULATION SCRIPT STARTED <<<")
    
    # --- 1. INSTITUTION & USERS ---
    print("\n[1] Setting up Institution & Users...")
    inst, _ = Institution.objects.get_or_create(
        name="UNIDAD EDUCATIVA DEMO",
        defaults={'ruc': '1790000000001', 'address': 'Av. Amazonas y Naciones Unidas'}
    )
    
    # Helper to create user
    def create_user(username, role, first, last, password="password123"):
        u, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@demo.com',
                'role': role,
                'institution': inst,
                'first_name': first,
                'last_name': last
            }
        )
        if created:
            u.set_password(password)
            u.save()
            print(f"    + Created User: {username} ({role})")
        else:
            print(f"    . Found User: {username}")
        return u

    admin = User.objects.filter(username='admin').first()
    if admin:
        if not admin.institution:
             admin.institution = inst
             admin.save()

    rector = create_user("rector_demo", "RECTOR", "Roberto", "Rector")
    teacher = create_user("profe_demo", "TEACHER", "Patricia", "Profesor")
    student = create_user("alumno_demo", "STUDENT", "Alex", "Alumno")
    parent = create_user("padre_demo", "PARENT", "Pablo", "Padre")

    # --- 2. ACADEMIC ---
    print("\n[2] Setting up Academic Module...")
    year, _ = AcademicYear.objects.get_or_create(
        institution=inst, year=2026,
        defaults={'name': 'Año Lectivo 2026-2027', 'start_date': '2026-05-01', 'end_date': '2027-02-28', 'is_active': True}
    )
    
    # Periods (Trimestres)
    periods_data = [
        # T1: May 2026 - Jul 2026
        (1, date(2026, 5, 1), date(2026, 7, 31)),
        # T2: Aug 2026 - Oct 2026
        (2, date(2026, 8, 1), date(2026, 10, 31)),
        # T3: Nov 2026 - Jan 2027
        (3, date(2026, 11, 1), date(2027, 1, 31))
    ]
    
    for num, start, end in periods_data:
        AcademicPeriod.objects.get_or_create(
            academic_year=year, number=num,
            defaults={
                'start_date': start,
                'end_date': end,
                'is_closed': False
            }
        )
    print("    . Academic Year & 3 Periods ready.")

    course, _ = Course.objects.get_or_create(
        institution=inst, name="10mo EGB A", year=year.year,
        defaults={'level': 'EGB_SUPERIOR', 'parallel': 'A'}
    )

    subject, _ = Subject.objects.get_or_create(
        course=course, name="Matemáticas",
        defaults={'teacher': teacher}
    )

    enrollment, _ = Enrollment.objects.get_or_create(
        student=student, course=course
    )
    print(f"    . Enrolled {student.username} in {course.name}")

    # Categories & Grades
    cat_hw, _ = EvaluationCategory.objects.get_or_create(
        subject=subject, name="Deberes", trimester=1, defaults={'weight': 30}
    )
    cat_exam, _ = EvaluationCategory.objects.get_or_create(
        subject=subject, name="Examen", trimester=1, defaults={'weight': 70}
    )
    
    Grade.objects.update_or_create(
        enrollment=enrollment, subject=subject, category=cat_hw,
        defaults={'score': 9.5, 'date': date.today(), 'observation': 'Buen trabajo'}
    )
    print("    . Grades recorded.")

    # --- 2.5 ACCOUNTING SETUP (Required for Treasury) ---
    print("\n[2.5] Setting up Accounting Module (Chart of Accounts)...")
    def create_account(code, name, type):
        acc, _ = Account.objects.get_or_create(
            institution=inst, code=code,
            defaults={'name': name, 'account_type': type, 'is_active': True}
        )
        return acc

    # Assets
    acc_caja = create_account('1.1.01', 'Caja General', 'ASSET')
    acc_banco = create_account('1.1.03', 'Banco Pichincha', 'ASSET')
    acc_cxc = create_account('1.1.02.01', 'Cuentas por Cobrar Clientes', 'ASSET')
    
    # Liabilities
    acc_iva_pay = create_account('2.1.01', 'IVA Cobrado', 'LIABILITY')
    
    # Income
    acc_income = create_account('4.1.01', 'Servicios Educativos', 'INCOME')
    
    # Config
    AccountingConfig.objects.get_or_create(institution=inst, key='ASSET_CASH', defaults={'account': acc_caja})
    AccountingConfig.objects.get_or_create(institution=inst, key='ASSET_BANK', defaults={'account': acc_banco})
    AccountingConfig.objects.get_or_create(institution=inst, key='ASSET_CXC', defaults={'account': acc_cxc})
    AccountingConfig.objects.get_or_create(institution=inst, key='LIABILITY_IVA', defaults={'account': acc_iva_pay})
    AccountingConfig.objects.get_or_create(institution=inst, key='INCOME_SERVICES', defaults={'account': acc_income})
    
    print("    . Accounting Plan & Config configured.")

    # --- 3. TREASURY ---
    print("\n[3] Setting up Treasury Module...")
    concept, _ = PaymentConcept.objects.get_or_create(
        institution=inst, name="Matrícula 2026",
        defaults={'price': Decimal("150.00"), 'iva_rate': Decimal("0.00")} # Education usually 0% IVA
    )
    
    method, _ = PaymentMethod.objects.get_or_create(
        institution=inst, name="Transferencia", defaults={'code': 'TRANSFER'}
    )
    
    # Create a Paid Charge
    charge, created_ch = Charge.objects.get_or_create(
        institution=inst, student=student, concept=concept,
        defaults={'amount': concept.price, 'due_date': date.today(), 'is_paid': False}
    )
    
    if not charge.is_paid:
        print("    . Processing Payment for Charge...")
        # Create Invoice
        seq = Invoice.objects.filter(institution=inst).count() + 1
        invoice = Invoice.objects.create(
            institution=inst,
            student=student,
            number=f"001-001-{seq:09d}",
            status='ISSUED',
            client_name="Pablo Padre",
            client_ruc="1717171717",
            payment_method=method,
            created_by=rector,
            subtotal_0=concept.price,
            subtotal_15=Decimal("0.00"),
            iva_total=Decimal("0.00"),
            total=concept.price
        )
        
        InvoiceDetail.objects.create(
            invoice=invoice, concept=concept, quantity=1, unit_price=concept.price, subtotal=concept.price, charge=charge
        )
        
        charge.is_paid = True
        charge.save()
        
        Payment.objects.create(invoice=invoice, amount_paid=invoice.total, verified=True)
        print(f"    + Invoice #{invoice.number} generated and paid.")
    else:
        print("    . Charge already paid.")

    # --- 4. COMMUNICATION ---
    print("\n[4] Setting up Communication Module...")
    
    # Check if Notice has institution field
    defaults = {
        'content': "Estamos emocionados de iniciar este nuevo periodo académico.",
        'author': rector,
        'target_role': 'ALL'
    }
    
    # Try to set institution if the model supports it (since I didn't see it in the view_file of models.py earlier, but it might be there or I missed it)
    # Looking at my previous view_file output for Notice...
    # class Notice(models.Model): ... author = ...
    # It does NOT have institution field visible in the snippet I saw? 
    # Wait, I see `class Notice(models.Model):` ... `author` ... `target_role`. 
    # It does NOT seem to have institution. It's properly filtered by author's institution usually.
    
    Notice.objects.get_or_create(
        title="Bienvenidos al Año Lectivo 2026",
        defaults=defaults
    )
    
    Message.objects.create(
        sender=rector, recipient=student,
        subject="Recordatorio de Documentos",
        body="Por favor acercarse a secretaría a entregar la carpeta."
    )
    print("    . Notice and Message created.")

    # --- 5. HELPDESK ---
    print("\n[5] Setting up Helpdesk Module...")
    wf, _ = Workflow.objects.get_or_create(institution=inst, name="Soporte General", defaults={'is_default': True})
    step, _ = PassStep.objects.get_or_create(workflow=wf, name="Revisión", defaults={'order': 1})
    
    cat_it, _ = ServiceCatalog.objects.get_or_create(
        institution=inst, name="Soporte IT",
        defaults={'sla_hours': 48, 'is_active': True}
    )
    
    Ticket.objects.create(
        institution=inst,
        requester=teacher,
        title="Proyector aula 10 no enciende",
        description="El proyector no da imagen.",
        category=cat_it,
        priority='HIGH',
        status='OPEN'
    )
    print("    . Support Ticket created.")

    # --- 6. PURCHASES ---
    print("\n[6] Setting up Purchases Module...")
    supplier, _ = Supplier.objects.get_or_create(
        institution=inst, tax_id="1799999999001",
        defaults={'legal_name': "PAPELERIA EL ESTUDIANTE", 'email': "ventas@papeleria.com"}
    )
    
    # Generic Expense Account
    acct, _ = Account.objects.get_or_create(
        institution=inst, code="5.1.01.01",
        defaults={'name': "Suministros de Oficina", 'account_type': 'EXPENSE'}
    )

    p_inv = PurchaseInvoice.objects.create(
        institution=inst,
        supplier=supplier,
        document_number=f"001-001-{random.randint(1000,9999)}",
        issue_date=date.today(),
        status='VALIDATED',
        created_by=rector,
        subtotal_15=Decimal("50.00"),
        iva=Decimal("7.50"),
        total=Decimal("57.50")
    )
    
    PurchaseItem.objects.create(
        invoice=p_inv, description="Resmas de papel", quantity=10, 
        unit_price=5.00, subtotal=50.00, tax_rate=15, expense_account=acct
    )
    print(f"    . Purchase Invoice {p_inv.document_number} created.")

    print("\n>>> POPULATION COMPLETADA CORRECTAMENTE <<<")
    print(f"Credenciales Demo (Si se crearon):")
    print(f"  Rector: rector_demo / password123")
    print(f"  Profe:  profe_demo  / password123")
    print(f"  Alumno: alumno_demo / password123")
    print(f"  Padre:  padre_demo  / password123")

if __name__ == '__main__':
    try:
        populate()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
