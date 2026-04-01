import os
import django
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Institution
from treasury.models import PaymentConcept, Charge, PaymentMethod
from payments.models import Transaction, PaymentGatewayConfig

def create_test_data():
    institution = Institution.objects.first()
    if not institution:
        print("No hay institución.")
        return

    # Buscar un estudiante
    student = User.objects.filter(role='STUDENT', institution=institution).first()
    if not student:
        print("No hay estudiantes en la BD.")
        return

    # Obtener o crear concepto
    concept, _ = PaymentConcept.objects.get_or_create(
        institution=institution,
        name="Pensión Mensual (Prueba Auto)",
        defaults={'price': Decimal('150.00'), 'iva_rate': Decimal('0.00')}
    )

    # Buscar método de pago 'Transferencia' o crear
    pm, _ = PaymentMethod.objects.get_or_create(
        institution=institution,
        name="Transferencia Creada Script",
        code="TRANSF_AUTO"
    )

    # Configuración de pasarela
    config, _ = PaymentGatewayConfig.objects.get_or_create(
        institution=institution,
        gateway_name='bank_transfer',
        defaults={'is_active': True, 'credentials': {'instructions': 'Banco de Pruebas Test'}}
    )

    print(f"Generando 5 transferencias en estado VERIFICANDO para el estudiante: {student.username}...")

    # Crear 5 transferencias pendientes
    for i in range(1, 6):
        # 1. Crear la Deuda (Charge)
        charge = Charge.objects.create(
            institution=institution,
            student=student,
            concept=concept,
            amount=Decimal(random.randint(50, 200)),
            due_date="2026-12-31",
            is_paid=False
        )
        
        # 2. Crear la Solicitud de Pago (Transaction VERIFYING)
        txn = Transaction.objects.create(
            user=student,
            amount=charge.amount,
            currency='USD',
            status='VERIFYING',
            gateway_name='bank_transfer',
            reference_id=str(charge.id), # Enlazar la transacción al id del charge
            description=f"Pago de Prueba #{i} - Transf. Bancaria"
        )
        print(f" -> Creado: Transacción ID #{txn.id} | Deuda ID #{charge.id} | Monto: ${txn.amount}")

    print("\n¡Listo! Ahora recargue la pantalla de Verificación de Transferencias en su panel de administración.")

if __name__ == '__main__':
    create_test_data()
