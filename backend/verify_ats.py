import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Institution
from accounting.sri.ats import ATSGenerator
from treasury.models import Invoice
from purchases.models import PurchaseInvoice, Supplier

def verify_ats():
    print("--- Verifying ATS Generator ---")
    
    institution = Institution.objects.first()
    if not institution:
        print("ERROR: No institution found.")
        return

    year = 2024
    month = 1 # January

    # 1. Ensure we have data (Using existing data from previous tests if available, otherwise script creates it)
    # Ideally prior scripts populated this. We will just run the generator.
    
    # 2. Generate
    print(f"Generating ATS for {year}-{month:02d}...")
    generator = ATSGenerator(institution, year, month)
    xml_output = generator.generate_xml()
    
    # 3. Output
    print("\n--- XML OUTPUT START ---")
    print(xml_output)
    print("--- XML OUTPUT END ---\n")
    
    # Simple Checks
    if "<iva>" in xml_output and "</iva>" in xml_output:
        print("SUCCESS: XML structure looks valid.")
    else:
        print("FAILURE: Invalid XML structure.")

    if "<compras>" in xml_output:
        print("SUCCESS: Contains comppras.")

    if "<ventas>" in xml_output:
        print("SUCCESS: Contains ventas.")

if __name__ == "__main__":
    verify_ats()
