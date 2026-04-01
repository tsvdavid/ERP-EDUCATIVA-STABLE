import os
import django
from decimal import Decimal
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounting.models import Bank, BankAccount, Account, JournalEntry, JournalItem
from users.models import Institution, User
from django.utils import timezone

def populate():
    print("Iniciando generación de datos para bancos...")
    
    # 1. Obtener la primera institución y el administrador que usaremos de creador
    institution = Institution.objects.first()
    if not institution:
        print("Error: No se encontró ninguna Institución en base de datos.")
        return
        
    user = User.objects.filter(role='ADMIN').first()
    if not user:
        user = User.objects.first()

    # 2. Crear Bancos
    nombres_bancos = ['Banco Pichincha', 'Banco Bolivariano', 'Produbanco']
    bancos = []
    for num, nombre in enumerate(nombres_bancos):
        banco, created = Bank.objects.get_or_create(
            institution=institution,
            name=nombre,
            defaults={'code': f'{nombre[:3].upper()}00{num}'}
        )
        bancos.append(banco)
        print(f"Banco {'creado' if created else 'existente'}: {banco.name}")

    # 3. Crear una cuenta contable padre "1.1.02 Bancos" si no existe
    cuenta_padre_bancos, _ = Account.objects.get_or_create(
        institution=institution,
        code='1.1.02',
        defaults={'name': 'Bancos', 'account_type': 'ASSET', 'level': 3}
    )

    # 4. Crear Cuentas Bancarias Operativas y sus Cuentas Contables en el Plan
    cuentas_bancarias = []
    for i, banco in enumerate(bancos):
        # Cuenta contable específica de este banco (Ej: 1.1.02.01)
        subcuenta_banco, _ = Account.objects.get_or_create(
            institution=institution,
            code=f'1.1.02.0{i+1}',
            defaults={
                'name': f'Cta. Cte. {banco.name}', 
                'account_type': 'ASSET', 
                'parent': cuenta_padre_bancos,
                'level': 4
            }
        )

        # Cuenta operativa del módulo tesorería/bancos
        cta_bancaria, created = BankAccount.objects.get_or_create(
            institution=institution,
            bank=banco,
            account_number=f'020055443{i}',
            defaults={
                'account_type': 'CHECKING',
                'linked_account': subcuenta_banco,
                'initial_balance': Decimal('15000.00')
            }
        )
        cuentas_bancarias.append(cta_bancaria)
        print(f"Cuenta Bancaria {'creada' if created else 'existente'}: {cta_bancaria.account_number} ({banco.name})")

    # 5. Generar algunos Asientos Contables para probar la conciliación
    print("\nGenerando movimientos (Ingresos y Gastos)...")
    
    # Cuentas de contrapartida
    cuenta_ingresos, _ = Account.objects.get_or_create(
        institution=institution,
        code='4.1.01',
        defaults={'name': 'Ingresos por Pensiones', 'account_type': 'INCOME', 'level': 3}
    )
    cuenta_gastos, _ = Account.objects.get_or_create(
        institution=institution,
        code='5.1.01',
        defaults={'name': 'Gastos Generales / Sueldos', 'account_type': 'EXPENSE', 'level': 3}
    )

    today = timezone.now().date()
    
    # Crear depósitos y pagos por cada banco
    for i, cta in enumerate(cuentas_bancarias):
        # Un depósito
        asiento_ingreso = JournalEntry.objects.create(
            institution=institution,
            date=today - timedelta(days=2),
            description=f"Depósito en Ventanilla - Cobro clientes ({cta.bank.name})",
            state='POSTED',
            created_by=user,
            reference=f"DEP-2026-00{i+1}"
        )
        # Débito al banco, crédito a ingresos
        JournalItem.objects.create(journal_entry=asiento_ingreso, account=cta.linked_account, debit=Decimal('3500.00'), credit=Decimal('0.00'), description='Ingreso a bancos')
        JournalItem.objects.create(journal_entry=asiento_ingreso, account=cuenta_ingresos, debit=Decimal('0.00'), credit=Decimal('3500.00'), description='Ingreso servicios')

        # Un pago/egreso
        asiento_gasto = JournalEntry.objects.create(
            institution=institution,
            date=today - timedelta(days=1),
            description=f"Pago a proveedores / Transferencia ({cta.bank.name})",
            state='POSTED',
            created_by=user,
            reference=f"TRF-100{i+1}"
        )
        # Débito a gastos, crédito al banco
        JournalItem.objects.create(journal_entry=asiento_gasto, account=cuenta_gastos, debit=Decimal('900.00'), credit=Decimal('0.00'), description='Pago servicios varios')
        JournalItem.objects.create(journal_entry=asiento_gasto, account=cta.linked_account, debit=Decimal('0.00'), credit=Decimal('900.00'), description='Salida de banco')

    print("✅ ¡Movimientos de prueba generados exitosamente en el Libro Diario!")
    print("Puedes revisar el balance base de las cuentas desde el sistema web.")

if __name__ == '__main__':
    populate()
