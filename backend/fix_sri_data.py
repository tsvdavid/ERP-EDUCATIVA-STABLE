import os
import django
import sys

sys.path.append(r'c:\Users\Soporte\Documents\PROYECTOS NETFORCE\ERP EDUCATIVA\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Institution
from treasury.models import Invoice

def fix_data():
    print("--- Corrigiendo Datos para Pruebas SRI ---")
    
    # Update Institution
    inst = Institution.objects.first()
    if not inst:
        print("Creando Institución por defecto...")
        inst = Institution.objects.create(name="UNIDAD EDUCATIVA TEST")
    
    print(f"Actualizando Institución: {inst.name}")
    inst.ruc = "1790000000001" # Test RUC
    inst.establishment_code = "001"
    inst.emission_point = "001"
    inst.sri_environment = 1 # Pruebas
    inst.address = "Av. Amazonas y Naciones Unidas"
    inst.obligado_contabilidad = True
    inst.save()
    print("  > RUC y Configuración SRI actualizados.")
    
    # Update Invoice
    inv = Invoice.objects.last()
    if inv:
        print(f"Actualizando Factura: {inv.number}")
        # Ensure it has this institution
        inv.institution = inst
        inv.client_ruc = "1710000000" # Valid Cédula length 10
        inv.client_name = "Consumidor Final"
        inv.status = 'ISSUED'
        inv.save()
        print("  > Factura asignada a institución correcta.")
    else:
        print("!!! No existen facturas. Por favor cree una desde el frontend o shell.")

if __name__ == "__main__":
    fix_data()
