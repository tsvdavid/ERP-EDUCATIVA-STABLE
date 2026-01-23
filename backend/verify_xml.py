import os
import django
import sys

# Setup Django Environment
sys.path.append(r'c:\Users\Soporte\Documents\PROYECTOS NETFORCE\ERP EDUCATIVA\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import Invoice
from treasury.sri.xml_generator import InvoiceXmlBuilder

def verify_xml_gen():
    print("--- Verificando Generación XML SRI ---")
    
    invoice = Invoice.objects.last()
    if not invoice:
        print("!!! No existen facturas para probar.")
        return

    print(f"Probando con Factura: {invoice.number}")
    
    try:
        builder = InvoiceXmlBuilder(invoice)
        access_key, xml_content = builder.build_xml()
        
        print("\n--- Clave de Acceso Generada ---")
        print(access_key)
        
        print("\n--- XML Generado (Primeros 500 chars) ---")
        print(xml_content[:500])
        
        # Simple validation
        if len(access_key) != 49:
             print("!!! ERROR: La clave de acceso debe tener 49 dígitos.")
        else:
             print(">>> OK: Clave tiene 49 dígitos.")
             
        if "<factura" in xml_content and "</factura>" in xml_content:
             print(">>> OK: Estructura XML básica detectada.")
        
        # Save to file for manual inspection
        with open('test_factura_sri.xml', 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(">>> XML guardado en test_factura_sri.xml")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"!!! Error: {e}")

if __name__ == "__main__":
    verify_xml_gen()
