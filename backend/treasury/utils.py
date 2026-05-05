from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.conf import settings
from django.db import transaction, IntegrityError
import logging

logger = logging.getLogger(__name__)

def get_next_invoice_number(institution, establishment, emission_point):
    """
    Genera el siguiente número de factura de forma segura y transaccional.
    Formato: 001-001-000000001
    """
    from .models import Invoice, InvoiceSequence
    
    # Asegurar que los códigos tengan el formato correcto (3 dígitos)
    est = str(establishment).zfill(3)
    pto = str(emission_point).zfill(3)
    
    # Reintentar una vez en caso de colisión externa (requisito 9)
    for attempt in range(2):
        try:
            with transaction.atomic():
                sequence, created = InvoiceSequence.objects.select_for_update().get_or_create(
                    institution=institution,
                    establishment=est,
                    emission_point=pto,
                    defaults={'next_number': 1}
                )
                
                if created:
                    # Sincronización inicial con facturas existentes si la secuencia es nueva
                    last_invoice = Invoice.objects.filter(
                        institution=institution,
                        number__startswith=f"{est}-{pto}-"
                    ).order_by('-number').first()
                    
                    if last_invoice:
                        try:
                            parts = last_invoice.number.split('-')
                            if len(parts) == 3:
                                sequence.next_number = int(parts[2]) + 1
                                sequence.save()
                        except (ValueError, IndexError):
                            pass
                
                current_seq = sequence.next_number
                invoice_number = f"{est}-{pto}-{current_seq:09d}"
                
                # Verificamos si por alguna razón externa ese número ya existe en Invoice
                if Invoice.objects.filter(number=invoice_number).exists():
                    # Si existe, saltamos a la siguiente secuencia real
                    last_real = Invoice.objects.filter(
                        number__startswith=f"{est}-{pto}-"
                    ).order_by('-number').first()
                    
                    if last_real:
                        parts = last_real.number.split('-')
                        sequence.next_number = int(parts[2]) + 1
                    else:
                        sequence.next_number += 1
                        
                    sequence.save()
                    # Reintentamos con el nuevo número
                    continue
                
                # Incrementamos para el siguiente
                sequence.next_number += 1
                sequence.save()
                
                return invoice_number
        except IntegrityError:
            if attempt == 0:
                continue
            raise

    raise Exception("No se pudo generar un número de factura único tras varios intentos.")

def generate_invoice_pdf(invoice):
    """
    Genera el PDF de una factura siguiendo el formato estándar de Eduka360.
    Retorna los bytes del PDF.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # --- HEADER (Institution Info) ---
    inst = invoice.institution
    
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, inst.name)
    
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 70, inst.address or "Dirección no registrada")
    c.drawString(50, height - 85, f"Tel: {inst.phone}  |  Email: {inst.email}")
    
    if hasattr(inst, 'obligado_contabilidad'):
        c.drawString(50, height - 100, f"Obligado a Llevar Contabilidad: {'SI' if inst.obligado_contabilidad else 'NO'}")
        
    # --- INVOICE BOX ---
    c.setLineWidth(1)
    c.rect(350, height - 130, 200, 100)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(360, height - 50, "R.U.C.: " + (inst.ruc if hasattr(inst, 'ruc') and inst.ruc else "9999999999999"))
    
    c.setFillColor(colors.lightgrey)
    c.rect(350, height - 80, 200, 25, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.drawString(360, height - 73, "F A C T U R A")
    
    c.setFont("Helvetica", 11)
    c.drawString(360, height - 100, f"No. {invoice.number}")
    c.setFont("Helvetica", 8)
    c.drawString(360, height - 120, f"AUTORIZACIÓN: {invoice.sri_status}")
    c.drawString(360, height - 130, f"CLAVE: {invoice.access_key or 'P-E-N-D-I-E-N-T-E'}")

    # --- CLIENT INFO ---
    y_client = height - 160
    c.roundRect(40, y_client - 60, 515, 60, 5, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y_client - 15, f"Razón Social:")
    c.setFont("Helvetica", 9)
    c.drawString(150, y_client - 15, invoice.client_name.upper())
    c.drawString(50, y_client - 30, f"Fecha: {invoice.issue_date.strftime('%d/%m/%Y')}")
    c.drawString(350, y_client - 30, f"RUC/CI: {invoice.client_ruc}")
    c.drawString(50, y_client - 45, f"Dirección: {invoice.client_address[:80]}")

    # --- DETAILS ---
    y_table = y_client - 90
    c.setFillColor(colors.lightgrey)
    c.rect(40, y_table, 515, 20, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.drawString(50, y_table + 6, "Cod.")
    c.drawString(130, y_table + 6, "Descripción")
    c.drawRightString(540, y_table + 6, "Total")
    
    y = y_table - 20
    for detail in invoice.details.all():
        c.setFont("Helvetica", 9)
        c.drawString(50, y, str(detail.concept.id))
        c.drawString(130, y, detail.concept.name[:50])
        c.drawRightString(540, y, f"{detail.subtotal:.2f}")
        y -= 15
        
    # --- TOTALS ---
    y_totals = y - 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(400, y_totals, "TOTAL USD:")
    c.drawRightString(540, y_totals, f"{invoice.total:.2f}")
    
    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
