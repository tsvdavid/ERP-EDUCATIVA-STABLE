import os
import django
from decimal import Decimal

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from purchases.models import Supplier, PurchaseLiquidation, PurchaseLiquidationItem
from users.models import Institution, User
from accounting.models import Account

def test_liquidation_cycle():
    print("Iniciando prueba de ciclo de Liquidaciones de Compra...")
    
    # 1. Setup - Get dependencies
    institution = Institution.objects.first()
    user = User.objects.filter(institution=institution).first()
    supplier = Supplier.objects.filter(institution=institution).first()
    expense_account = Account.objects.filter(institution=institution, account_type='EXPENSE').first()
    
    if not all([institution, user, supplier]):
        print("Faltan datos básicos para correr la prueba (Institution, User, Supplier).")
        return
        
    print(f"Utilizando proveedor: {supplier.legal_name}")
    
    # 2. Recrear Data en Diccionario (simulando vista DRF)
    from purchases.serializers import PurchaseLiquidationSerializer
    
    data = {
        "supplier": supplier.id,
        "document_number": "001-001-999999999",
        "authorization_code": "1234567890",
        "issue_date": "2024-03-01",
        "sustento_tributario": "01",
        "payment_method": "20",
        "items": [
            {
                "description": "Servicio de Limpieza",
                "expense_account": expense_account.id if expense_account else None,
                "quantity": "2.00",
                "unit_price": "50.00",
                "tax_rate": "15" # $100 subtotal -> $15 IVA
            },
            {
                "description": "Suministros varios",
                "expense_account": expense_account.id if expense_account else None,
                "quantity": "1.00",
                "unit_price": "20.00",
                "tax_rate": "0" # $20 subtotal
            }
        ]
    }
    
    # Simular la petición del serializador (que lo hace Create en la View)
    serializer = PurchaseLiquidationSerializer(data=data)
    if serializer.is_valid():
        liq = serializer.save(institution=institution, created_by=user)
        print(f"Liquidación Creada Exitosamente: ID {liq.id}")
        print(f"Totales Calculados:")
        print(f"Subtotal 15%: ${liq.subtotal_15}")
        print(f"Subtotal 0%:  ${liq.subtotal_0}")
        print(f"IVA:        ${liq.iva}")
        print(f"Total:      ${liq.total}")
        
        # Verify correctness
        assert liq.subtotal_15 == Decimal('100.00')
        assert liq.subtotal_0 == Decimal('20.00')
        assert liq.iva == Decimal('15.00')
        assert liq.total == Decimal('135.00')
        
        print("Cálculos verificados correctamente.")
        
        # 3. Validarla
        liq.status = 'VALIDATED'
        liq.save()
        print(f"Liquidación Validada. Estado: {liq.status}")
        
        # Cleanup
        liq.delete()
        print("Limpieza: Registro de prueba eliminado satisfactoriamente.")
    else:
        print("Error en el Serializer:", serializer.errors)

if __name__ == '__main__':
    test_liquidation_cycle()
