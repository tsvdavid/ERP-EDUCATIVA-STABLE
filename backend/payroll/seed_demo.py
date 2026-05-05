import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Institution
from payroll.models import Employee, Contract, WorkShift, Department, Position
from accounting.models import Account, AccountingConfig

def seed_payroll_demo():
    print("Iniciando seed de Nómina...")
    
    inst = Institution.objects.first()
    admin = User.objects.filter(institution=inst, role='ADMIN').first()
    
    if not inst:
        print("Error: No hay instituciones en el sistema.")
        return

    # 1. Configuración Contable para Nómina
    # Asegurar que existan cuentas de gasto y pasivo
    def get_or_create_account(code, name, acc_type):
        acc, _ = Account.objects.get_or_create(
            institution=inst, code=code, 
            defaults={'name': name, 'account_type': acc_type}
        )
        return acc

    salary_exp = get_or_create_account('5.1.01', 'Gasto Sueldos', 'EXPENSE')
    social_exp = get_or_create_account('5.1.02', 'Gasto Aporte Patronal', 'EXPENSE')
    salary_pay = get_or_create_account('2.1.05', 'Sueldos por Pagar', 'LIABILITY')
    iess_pay = get_or_create_account('2.1.06', 'IESS por Pagar', 'LIABILITY')

    configs = [
        ('EXPENSE_SALARIES', salary_exp),
        ('EXPENSE_SOCIAL_SECURITY', social_exp),
        ('LIABILITY_SALARIES_PAYABLE', salary_pay),
        ('LIABILITY_IESS_PAYABLE', iess_pay),
    ]

    for key, acc in configs:
        AccountingConfig.objects.update_or_create(
            institution=inst, key=key, defaults={'account': acc}
        )

    # 2. Estructura RRHH
    dept, _ = Department.objects.get_or_create(institution=inst, name='Académico', code='ACAD')
    pos, _ = Position.objects.get_or_create(institution=inst, department=dept, name='Docente Principal')
    shift, _ = WorkShift.objects.get_or_create(
        institution=inst, name='Jornada Completa', 
        start_time='08:00', end_time='16:30'
    )

    # 3. Crear Empleado de Prueba (asociado a un User existente o nuevo)
    test_user = User.objects.filter(role='STUDENT').first() # Reusamos uno para el demo
    if not test_user:
        test_user = User.objects.create_user(
            username='empleado_test', password='password123',
            first_name='Juan', last_name='Pérez',
            email='juan.perez@test.com', institution=inst, role='STUDENT'
        )

    emp, _ = Employee.objects.get_or_create(
        institution=inst, user=test_user,
        defaults={
            'identification': '1712345678',
            'birth_date': date(1990, 5, 20),
            'gender': 'M'
        }
    )

    # 4. Crear Contrato
    Contract.objects.get_or_create(
        institution=inst, employee=emp,
        defaults={
            'position': pos,
            'shift': shift,
            'base_salary': Decimal('1200.00'),
            'start_date': date(2024, 1, 1),
            'is_active': True
        }
    )

    print("Seed de Nómina completado exitosamente.")

if __name__ == '__main__':
    seed_payroll_demo()
