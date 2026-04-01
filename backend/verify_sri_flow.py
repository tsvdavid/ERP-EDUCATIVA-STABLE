import os
import django
import sys

sys.path.append(r'c:\Users\Soporte\Documents\PROYECTOS NETFORCE\Eduka360\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import Invoice
from treasury.sri.xml_generator import InvoiceXmlBuilder
from treasury.sri.signer import XadesSigner

def verify_full_flow():
    print("--- Verificando Flujo Completo (Sin Envío Real) ---")
    
    invoice = Invoice.objects.last()
    if not invoice:
        print("!!! No existen facturas.")
        return

    # 1. Generar XML
    try:
        print(f"Generando XML para: {invoice.number}")
        builder = InvoiceXmlBuilder(invoice)
        access_key, xml_content = builder.build_xml()
        print(">>> XML Generado OK")
        print(f"Clave: {access_key}")
    except Exception as e:
        print(f"!!! Error Generando XML: {e}")
        return

    # 2. Firmar (Esto fallará si no hay archivo .p12 real configurado)
    inst = invoice.institution
    if inst.electronic_signature and os.path.exists(inst.electronic_signature.path):
        try:
            print(f"Intentando firmar con: {inst.electronic_signature.path}")
            pwd = inst.signature_password
            signer = XadesSigner(inst.electronic_signature.path, pwd)
            signed_xml = signer.sign_xml(xml_content)
            print(">>> Firma Exitosa!")
            print(signed_xml[:300])
        except Exception as e:
            print(f"!!! Error al firmar (Esperado si la firma es dummy): {e}")
    else:
        print(">>> No hay firma electrónica configurada. Saltando paso de firma.")
        print("Para probar firma, suba un .p12 válido a la institución.")

if __name__ == "__main__":
    verify_full_flow()
