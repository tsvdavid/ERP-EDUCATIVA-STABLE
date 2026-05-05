import os
import django
import sys
import base64

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import Invoice
from treasury.sri.xml_generator import InvoiceXmlBuilder
from treasury.sri.signer import XadesSigner
from treasury.sri.client import SriClient

def validate_sri():
    # Targeted invoice for institution with signature
    invoice = Invoice.objects.filter(institution_id=18).last()
    if not invoice:
        print("FAIL Stage 0: No invoice found for institution 18")
        return

    print(f"--- VALIDATING SRI FLOW FOR INVOICE: {invoice.number} ---")
    inst = invoice.institution

    # 1. Load Certificate
    print("Stage 1: Load Certificate")
    if not inst.electronic_signature:
        print("FAIL Stage 1: No electronic signature file in DB")
        return
    cert_path = inst.electronic_signature.path
    if not os.path.exists(cert_path):
        print(f"FAIL Stage 1: Certificate file not found at {cert_path}")
        return
    print("PASS Stage 1: Certificate file exists")

    # 2. Decrypt/Init Signer
    print("Stage 2: Init Signer")
    try:
        signer = XadesSigner(cert_path, inst.signature_password)
        print("PASS Stage 2: Signer initialized (Certificate decrypted)")
    except Exception as e:
        print(f"FAIL Stage 2: Signer init error: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Generate XML
    print("Stage 3: Generate XML")
    try:
        builder = InvoiceXmlBuilder(invoice)
        access_key, xml_content = builder.build_xml()
        print(f"PASS Stage 3: XML generated. Access Key: {access_key}")
    except Exception as e:
        print(f"FAIL Stage 3: XML generation error: {e}")
        return

    # 4. Sign XML
    print("Stage 4: Sign XML")
    try:
        # Use simple string for signing
        signed_xml = signer.sign_xml(xml_content)
        print("PASS Stage 4: XML signed successfully")
        # print(signed_xml[:500])
    except Exception as e:
        print(f"FAIL Stage 4: XML signing error: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Send to SRI Reception (Test)
    print("Stage 5: SRI Reception")
    client = SriClient(environment=1) # 1 for Test
    success, msg, status = client.send_receipt(signed_xml)
    print(f"Result: Success={success}, Msg={msg}, Status={status}")
    if success:
        print("PASS Stage 5: SRI Reception accepted")
    else:
        print(f"FAIL Stage 5: SRI Reception error: {msg}")
        return

    # 6. Poll Authorization
    print("Stage 6: SRI Authorization")
    success, msg, status, raw = client.request_authorization(access_key)
    print(f"Result: Success={success}, Msg={msg}, Status={status}")
    if success:
        print("PASS Stage 6: SRI Authorized")
    else:
        print(f"INFO Stage 6: SRI Status: {status}. Message: {msg}")
        if raw:
            # Look for <mensaje> tags in raw response
            import re
            mensajes = re.findall(r'<mensaje>(.*?)</mensaje>', raw)
            if mensajes:
                print(f"SRI Details: {mensajes}")

if __name__ == "__main__":
    validate_sri()
