
import os
import sys
import django
import random
from decimal import Decimal
from datetime import date, timedelta, datetime
from faker import Faker

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from users.models import User, Institution
from academic.models import AcademicYear, AcademicPeriod, Course, Subject, Enrollment, Grade, EvaluationCategory, Attendance
from treasury.models import PaymentConcept, PaymentMethod, Charge, Invoice, Payment, InvoiceDetail, StudentAccount
from communication.models import Notice, Message
from helpdesk.models import ServiceCatalog, Ticket, PassStep, Workflow
from health.models import MedicalRecord, DeceRecord, BehaviorRecord, BehaviorCase, CaseFollowUp, StudentRiskProfile, AlertRule
from procedures.models import ProcedureTemplate, StudentRequest
from accounting.models import Account, AccountingConfig

fake = Faker(['es_ES'])

def run_simulation(reset=False):
    print("🚀 >>> SIMULACIÓN COMPLETA DE AÑO LECTIVO INICIADA <<<")
    
    if reset:
        print("⚠️  Limpiando base de datos existente...")
        Institution.objects.exclude(name="Eduka360 Pro").delete() 
        User.objects.exclude(is_superuser=True).delete()

    institutions_data = [
        {"name": "Colegio Técnico Innovación", "ruc": "1790000000001", "type": "TECNICO"},
        {"name": "Unidad Educativa Luz del Saber", "ruc": "1790000000002", "type": "TRADICIONAL"},
        {"name": "Tech Academy", "ruc": "1790000000003", "type": "ACADEMIA"}
    ]

    for inst_info in institutions_data:
        print(f"\n🏢 Procesando Institución: {inst_info['name']}")
        inst, _ = Institution.objects.get_or_create(
            name=inst_info['name'],
            defaults={'ruc': inst_info['ruc'], 'address': fake.address()}
        )

        # --- CONTABILIDAD (NUEVO: Necesario para Invoicing) ---
        print("   [0] Configurando Contabilidad (Plan de Cuentas)...")
        def get_or_create_account(code, name, type):
            acc, _ = Account.objects.get_or_create(
                institution=inst, code=code,
                defaults={'name': name, 'account_type': type, 'is_active': True}
            )
            return acc

        acc_caja = get_or_create_account('1.1.01', 'Caja General', 'ASSET')
        acc_banco = get_or_create_account('1.1.03', 'Banco Pichincha', 'ASSET')
        acc_cxc = get_or_create_account('1.1.02.01', 'Cuentas por Cobrar Clientes', 'ASSET')
        acc_iva_pay = get_or_create_account('2.1.01', 'IVA Cobrado', 'LIABILITY')
        acc_income = get_or_create_account('4.1.01', 'Servicios Educativos', 'INCOME')
        
        # Configuración obligatoria
        conf_data = [
            ('ASSET_CASH', acc_caja), ('ASSET_BANK', acc_banco), 
            ('ASSET_CXC', acc_cxc), ('LIABILITY_IVA', acc_iva_pay), 
            ('INCOME_SERVICES', acc_income)
        ]
        for key, acc in conf_data:
            AccountingConfig.objects.get_or_create(institution=inst, key=key, defaults={'account': acc})

        # --- STAFF ---
        def create_staff(username, role, first, last):
            u, created = User.objects.get_or_create(
                username=f"{username}_{inst.id}",
                defaults={
                    'email': f'{username}_{inst.id}@eduka360.com',
                    'role': role,
                    'institution': inst,
                    'first_name': first,
                    'last_name': last
                }
            )
            if created: u.set_password("password123"); u.save()
            return u

        rector = create_staff("rector", "RECTOR", fake.first_name(), fake.last_name())
        admin = create_staff("admin", "LOCAL_ADMIN", fake.first_name(), fake.last_name())
        dece = create_staff("dece", "DECE", fake.first_name(), fake.last_name())
        medico = create_staff("medico", "MEDICO", fake.first_name(), fake.last_name())
        contador = create_staff("contador", "ACCOUNTANT", fake.first_name(), fake.last_name())

        teachers = []
        for i in range(10):
            teachers.append(create_staff(f"profe_{i}", "TEACHER", fake.first_name(), fake.last_name()))

        print("   [2] Configurando Año Lectivo...")
        ayear, _ = AcademicYear.objects.get_or_create(
            institution=inst, year=2026,
            defaults={'name': f'Año Lectivo {inst.name} 2026', 'start_date': date(2026, 5, 1), 'end_date': date(2027, 2, 28), 'is_active': True}
        )

        periods = []
        for n, start, end in [(1, date(2026,5,1), date(2026,7,31)), (2, date(2026,8,1), date(2026,10,31)), (3, date(2026,11,1), date(2027,1,31))]:
            p, _ = AcademicPeriod.objects.get_or_create(academic_year=ayear, number=n, defaults={'start_date': start, 'end_date': end})
            periods.append(p)

        courses = []
        for level in ['8vo EGB', '9no EGB', '10mo EGB']:
            for par in ['A', 'B']:
                c, _ = Course.objects.get_or_create(institution=inst, name=f"{level} {par}", year=2026, defaults={'level': 'EGB_SUPERIOR', 'parallel': par})
                courses.append(c)

        subject_names = ["Matemáticas", "Lenguaje", "Ciencias Naturales", "Estudios Sociales", "Inglés"]
        subjects = []
        for c in courses:
            for sname in subject_names:
                s, _ = Subject.objects.get_or_create(course=c, name=sname, defaults={'teacher': random.choice(teachers)})
                subjects.append(s)

        print(f"   [3] Generando 50 Estudiantes...")
        students = []
        enrollments = []
        for i in range(50):
            username = f"student_{inst.id}_{i}"
            s, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@student.com",
                    'role': "STUDENT",
                    'institution': inst,
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name()
                }
            )
            if created:
                s.set_password("password123")
                s.save()
            students.append(s)
            
            MedicalRecord.objects.get_or_create(student=s)
            DeceRecord.objects.get_or_create(student=s, defaults={'special_educational_needs': random.choice([True, False, False, False])})
            StudentAccount.objects.get_or_create(student=s, institution=inst) 

            target_course = random.choice(courses)
            e, _ = Enrollment.objects.get_or_create(student=s, course=target_course)
            enrollments.append(e)

        print("   [4] Simulando Notas y Asistencia...")
        eval_cats = []
        for s in subjects:
            for p in periods:
                c1, _ = EvaluationCategory.objects.get_or_create(subject=s, name="Deberes", trimester=p.number, defaults={'weight': 40})
                c2, _ = EvaluationCategory.objects.get_or_create(subject=s, name="Exámenes", trimester=p.number, defaults={'weight': 60})
                eval_cats.extend([c1, c2])

        for e in enrollments:
            e_subjects = [sub for sub in subjects if sub.course == e.course]
            for sub in e_subjects:
                for p_num in [1, 2]:
                    cats = [c for c in eval_cats if c.subject == sub and c.trimester == p_num]
                    for cat in cats:
                        if not Grade.objects.filter(enrollment=e, subject=sub, category=cat).exists():
                            base_score = 4.0 if random.random() < 0.1 else 7.5
                            score = min(10.0, base_score + random.random() * 3)
                            Grade.objects.create(enrollment=e, subject=sub, category=cat, score=score, date=date(2026, 6, 15) if p_num==1 else date(2026, 9, 15))

            for d in range(10): 
                Attendance.objects.get_or_create(
                    enrollment=e, 
                    date=date(2026, 5, 2) + timedelta(days=d), 
                    defaults={'status': random.choices(['PRESENT', 'ABSENT', 'LATE'], weights=[85, 10, 5])[0]}
                )

        print("   [5] Generando Casos DECE y Vigilancia...")
        for e in enrollments[:5]: 
            record, _ = BehaviorRecord.objects.get_or_create(
                student=e.student, academic_year=ayear, record_type='NEGATIVE_SEVERE',
                template='FIGHTS', defaults={'created_by': random.choice(teachers), 'description': "Involucrado en altercado."}
            )
            case, created = BehaviorCase.objects.get_or_create(
                student=e.student, academic_year=ayear, area='DECE', title="Seguimiento Conductual",
                defaults={'description': "Derivado por incidente.", 'assigned_to': dece, 'created_by': admin}
            )
            if created:
                case.behavior_records.add(record)
                CaseFollowUp.objects.create(case=case, follow_up_type='INTERVIEW_STUDENT', content="Entrevista realizada.", created_by=dece)

        print("   [6] Generando Facturación y Pagos...")
        concept_pension, _ = PaymentConcept.objects.get_or_create(institution=inst, name="Pensión Mensual", defaults={'price': Decimal("200.00"), 'iva_rate': 0})
        method = PaymentMethod.objects.filter(institution=inst).first() or PaymentMethod.objects.create(institution=inst, name="Efectivo", code="CASH")

        for s in students[:10]: 
            charge, _ = Charge.objects.get_or_create(institution=inst, student=s, concept=concept_pension, due_date=date(2026, 5, 5), defaults={'amount': 200})
            
            if not charge.is_paid and random.random() < 0.7:
                inv_num = f"INV-{inst.id}-{s.id}"
                if not Invoice.objects.filter(number=inv_num).exists():
                    inv = Invoice.objects.create(
                        institution=inst, student=s, number=inv_num,
                        status='ISSUED', total=200, subtotal_0=200, created_by=contador,
                        client_name=f"{s.first_name} {s.last_name}", client_ruc="1799999999",
                        payment_method=method
                    )
                    InvoiceDetail.objects.create(invoice=inv, concept=concept_pension, quantity=1, unit_price=200, subtotal=200, charge=charge)
                    Payment.objects.create(invoice=inv, amount_paid=200, verified=True)
                    charge.is_paid = True; charge.save()

        print("   [7] Generando Tickets de Soporte...")
        cat_it, _ = ServiceCatalog.objects.get_or_create(institution=inst, name="Soporte Técnico", defaults={'sla_hours': 24})
        if not Ticket.objects.filter(institution=inst, requester__institution=inst).exists():
            Ticket.objects.create(
                institution=inst, requester=random.choice(teachers),
                title="Problema con Plataforma Notas", description="No puedo cargar notas.",
                category=cat_it, priority='MEDIUM', status='OPEN'
            )

    print("\n✅ >>> SIMULACIÓN FINALIZADA CON ÉXITO <<<")

if __name__ == "__main__":
    run_simulation(reset=False)
