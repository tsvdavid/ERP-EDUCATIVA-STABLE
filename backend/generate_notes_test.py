import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from purchases.models import PurchaseInvoice, PurchaseCreditNote, PurchaseDebitNote
from users.models import User, Institution

def run():
    print("Iniciando generación de Notas de Crédito y Débito de prueba...")
    
    # Obtener el primer usuario administrador y su institución
    user = User.objects.filter(role__in=['ADMIN', 'LOCAL_ADMIN']).first()
    if not user:
        print("No se encontró ningún usuario administrador.")
        return
        
    institution = user.institution
    if not institution:
        print("El usuario encontrado no tiene una institución asignada.")
        return

    # Buscar una factura validada. Si no hay, buscamos cualquiera.
    invoices = PurchaseInvoice.objects.filter(status='VALIDATED', institution=institution)
    if not invoices.exists():
        print("No se encontraron facturas en estado VALIDATED. Buscando cualquier factura...")
        invoices = PurchaseInvoice.objects.filter(institution=institution)
        if not invoices.exists():
            print("No se encontraron facturas en el sistema. Debe crear al menos una Factura de Compra antes de generar Notas.")
            return

    invoice = invoices.first()
    
    # 1. Crear Nota de Crédito de Prueba
    cn_number = "001-003-000000777"
    cn, created_cn = PurchaseCreditNote.objects.get_or_create(
        document_number=cn_number,
        defaults={
            'institution': institution,
            'invoice': invoice,
            'authorization_code': "1234567890123456789012345678901234567890123456789",
            'issue_date': "2024-03-10",
            'reason': "Devolución de material de oficina dañado (Prueba)",
            'subtotal_0': Decimal('0.00'),
            'subtotal_15': Decimal('150.00'),
            'subtotal_no_obj': Decimal('0.00'),
            'iva': Decimal('22.50'),
            'created_by': user
        }
    )
    if created_cn:
        print(f"✅ Nota de Crédito generada exitosamente: {cn}")
    else:
        print(f"⚠️ La Nota de Crédito {cn_number} ya existía en la base de datos.")

    # 2. Crear Nota de Débito de Prueba
    dn_number = "001-003-000000888"
    dn, created_dn = PurchaseDebitNote.objects.get_or_create(
        document_number=dn_number,
        defaults={
            'institution': institution,
            'invoice': invoice,
            'authorization_code': "9876543210987654321098765432109876543210987654321",
            'issue_date': "2024-03-12",
            'reason': "Recargo adicional por costo de envío logístico (Prueba)",
            'subtotal_0': Decimal('35.00'),
            'subtotal_15': Decimal('0.00'),
            'subtotal_no_obj': Decimal('0.00'),
            'iva': Decimal('0.00'), # Tarifa 0%
            'created_by': user
        }
    )
    if created_dn:
        print(f"✅ Nota de Débito generada exitosamente: {dn}")
    else:
        print(f"⚠️ La Nota de Débito {dn_number} ya existía en la base de datos.")

if __name__ == '__main__':
    run()
