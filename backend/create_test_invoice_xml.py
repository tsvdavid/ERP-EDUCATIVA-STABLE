import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from treasury.models import Invoice, PaymentMethod, PaymentConcept, InvoiceDetail
from users.models import User, Institution

def create_test_invoice():
    # Get First Institution
    inst = Institution.objects.first()
    if not inst:
        print("Error: No Institution found.")
        return

    # Get First Student
    student = User.objects.filter(role='STUDENT').first()
    if not student:
        # Create dummy student if needed
        student = User.objects.create_user(username='teststudent', password='password123', role='STUDENT', first_name='Test', last_name='Student', email='test@example.com')
        student.institution = inst
        student.save()

    # Get Payment Method
    pm = PaymentMethod.objects.first()
    if not pm:
        pm = PaymentMethod.objects.create(name="Efectivo", code="01", institution=inst)

    # Get Concept
    concept = PaymentConcept.objects.first()
    if not concept:
        concept = PaymentConcept.objects.create(name="Matricula Test", price=100.00, institution=inst)

    # XML Content Mock
    dummy_xml = """<?xml version="1.0" encoding="UTF-8"?>
<factura version="2.1.0" id="comprobante">
    <infoTributaria>
        <ambiente>1</ambiente>
        <tipoEmision>1</tipoEmision>
        <razonSocial>ESCUELA TEST</razonSocial>
        <ruc>1790085783001</ruc>
        <claveAcceso>0101202601179008578300110010010000000011234567819</claveAcceso>
        <estab>001</estab>
        <ptoEmi>001</ptoEmi>
        <secuencial>000000999</secuencial>
        <dirMatriz>Quito, Ecuador</dirMatriz>
    </infoTributaria>
    <infoFactura>
        <fechaEmision>01/01/2026</fechaEmision>
        <dirEstablecimiento>Quito, Ecuador</dirEstablecimiento>
        <obligadoContabilidad>NO</obligadoContabilidad>
        <tipoIdentificacionComprador>05</tipoIdentificacionComprador>
        <razonSocialComprador>Juan Perez</razonSocialComprador>
        <identificacionComprador>1712345678</identificacionComprador>
        <totalSinImpuestos>100.00</totalSinImpuestos>
        <totalDescuento>0.00</totalDescuento>
        <propina>0.00</propina>
        <importeTotal>100.00</importeTotal>
        <moneda>DOLAR</moneda>
    </infoFactura>
    <detalles>
        <detalle>
            <codigoPrincipal>001</codigoPrincipal>
            <descripcion>Matricula Test</descripcion>
            <cantidad>1.00</cantidad>
            <precioUnitario>100.00</precioUnitario>
            <descuento>0.00</descuento>
            <precioTotalSinImpuesto>100.00</precioTotalSinImpuesto>
        </detalle>
    </detalles>
</factura>"""

    # Create Invoice
    inv = Invoice.objects.create(
        institution=inst,
        student=student,
        number="001-001-000000999",
        status='ISSUED',
        sri_status='AUTHORIZED', # Important: Authorized
        sri_authorization_date=timezone.now(),
        xml_content=dummy_xml,
        access_key="0101202601179008578300110010010000000011234567819",
        client_name="Juan Perez",
        client_ruc="1712345678",
        subtotal_0=100.00,
        total=100.00,
        payment_method=pm,
        created_by=student # technically created by admin but using student for simplicity
    )

    InvoiceDetail.objects.create(
        invoice=inv,
        concept=concept,
        quantity=1,
        unit_price=100.00,
        subtotal=100.00
    )

    print(f"Factura de prueba creada: {inv.number} (ID: {inv.id})")

if __name__ == '__main__':
    create_test_invoice()
