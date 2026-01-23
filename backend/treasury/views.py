from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from io import BytesIO
import datetime

from .models import PaymentConcept, PaymentMethod, Invoice, InvoiceDetail, Payment, StudentAccount, Charge
from .serializers import (
    PaymentConceptSerializer, PaymentMethodSerializer, 
    InvoiceSerializer, CreateInvoiceSerializer, StudentAccountSerializer, ChargeSerializer
)
from users.models import User, Institution

class PaymentConceptViewSet(viewsets.ModelViewSet):
    queryset = PaymentConcept.objects.filter(is_active=True)
    serializer_class = PaymentConceptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

class StudentAccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentAccount.objects.all().select_related('student', 'student__institution')
    serializer_class = StudentAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'STUDENT':
            return StudentAccount.objects.filter(student=user).select_related('student', 'student__institution')
        elif user.role == 'PARENT':
            # Accounts of children
            children_ids = user.children.values_list('id', flat=True)
            return StudentAccount.objects.filter(student__id__in=children_ids).select_related('student', 'student__institution')
        return super().get_queryset()

class ChargeViewSet(viewsets.ModelViewSet):
    queryset = Charge.objects.all().select_related('student', 'concept', 'institution')
    serializer_class = ChargeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Base optimization
        queryset = Charge.objects.all().select_related('student', 'concept', 'institution')
        user = self.request.user
        
        # Security
        if user.role == 'STUDENT':
             queryset = queryset.filter(student=user)
        elif user.role == 'PARENT':
             queryset = queryset.filter(student__in=user.children.all())
        
        # Filters
        student_id = self.request.query_params.get('student_id')
        if student_id:
             queryset = queryset.filter(student_id=student_id)
             
        pending = self.request.query_params.get('pending')
        if pending == 'true':
            queryset = queryset.filter(is_paid=False)
            
        return queryset

    @action(detail=False, methods=['post'], url_path='generate-monthly')
    def generate_monthly(self, request):
        """
        Generate charges for a concept for a list of students or a course.
        {
            "concept_id": 1,
            "due_date": "2026-02-05",
            # Option A: List of student IDs
            "student_ids": [1, 2, 3], 
            # Option B: Course ID (to get all students)
            "course_id": 5
        }
        """
        data = request.data
        concept_id = data.get('concept_id')
        due_date = data.get('due_date')
        
        try:
            concept = PaymentConcept.objects.get(pk=concept_id)
            students = []
            
            if data.get('student_ids'):
                students = User.objects.filter(id__in=data['student_ids'])
            elif data.get('course_id'):
                from academic.models import Enrollment
                # Get students enrolled in this course
                enrollments = Enrollment.objects.filter(course_id=data['course_id']).select_related('student')
                students = [e.student for e in enrollments]
            
            created_count = 0
            charges_to_create = []
            for student in students:
                 # Check duplicate? Maybe same concept same month?
                 # For now, just create.
                 charges_to_create.append(Charge(
                    institution=student.institution,
                    student=student,
                    concept=concept,
                    amount=concept.price,
                    due_date=due_date,
                    is_paid=False
                 ))
            
            Charge.objects.bulk_create(charges_to_create)
            created_count = len(charges_to_create)
                
            return Response({'message': f'Se generaron {created_count} cargos.'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().select_related('institution', 'student', 'payment_method').prefetch_related('details', 'details__concept')
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Optimized base queryset
        queryset = Invoice.objects.all().select_related('institution', 'student', 'payment_method').prefetch_related('details', 'details__concept').order_by('-id')

        if user.role in ['STUDENT', 'PARENT']:
             # Can only see own invoices
             if user.role == 'STUDENT':
                 return queryset.filter(student=user)
             else:
                 children_ids = user.children.values_list('id', flat=True)
                 return queryset.filter(student__id__in=children_ids)
        
        # Admin / Treasury: Allow filtering
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
            
        return queryset

    @action(detail=False, methods=['post'], url_path='process-payment')
    @transaction.atomic
    def process_payment(self, request):
        """
        Receives:
        {
            "student_id": 1,
            "payment_method_id": 2,
            "concepts": [
                {"concept_id": 1, "quantity": 1, "charge_id": 10},
                {"concept_id": 2, "quantity": 1}
            ]
        }
        """
        serializer = CreateInvoiceSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                student = User.objects.get(pk=data['student_id'])
                pay_method = PaymentMethod.objects.get(pk=data['payment_method_id'])
                
                # Create Invoice Header
                last_invoice = Invoice.objects.filter(institution=student.institution).order_by('-id').first()
                
                # Default SRI config
                inst = student.institution
                est = inst.establishment_code if hasattr(inst, 'establishment_code') else '001'
                pto = inst.emission_point if hasattr(inst, 'emission_point') else '001'
                
                seq = 1
                if last_invoice:
                    # Try to parse last sequence
                    # Formatos: "000000005" o "001-001-000000005"
                    parts = last_invoice.number.split('-')
                    if len(parts) == 3:
                        try:
                            seq = int(parts[2]) + 1
                        except:
                            pass
                    elif last_invoice.number.isdigit():
                        seq = int(last_invoice.number) + 1
                
                # Format: 001-001-000000001
                invoice_number = f"{est}-{pto}-{seq:09d}" 
                
                invoice = Invoice.objects.create(
                    institution=student.institution or PaymentConcept.objects.first().institution, # Fallback
                    student=student,
                    number=invoice_number,
                    status='ISSUED',
                    client_name=data.get('client_name', f"{student.first_name} {student.last_name}"),
                    client_ruc=data.get('client_ruc', student.cedula or '9999999999999'),
                    client_address=data.get('client_address') or student.address or 'Sin dirección',
                    client_email=data.get('client_email') or student.email or '',
                    payment_method=pay_method,
                    created_by=request.user
                )

                # UPDATE STUDENT PROFILE with new billing info if provided
                profile_updated = False
                new_address = data.get('client_address')
                new_email = data.get('client_email')
                
                if new_address and new_address != student.address:
                    student.address = new_address
                    profile_updated = True
                
                if new_email and new_email != student.email:
                    student.email = new_email
                    profile_updated = True

                if profile_updated:
                    student.save()

                total_0 = 0
                total_15 = 0
                total_iva = 0
                
                # Create Details
                for item in data['concepts']:
                    concept = PaymentConcept.objects.get(pk=item['concept_id'])
                    qty = item.get('quantity', 1)
                    
                    # Determine price: from charge if exists (snapshot) or current concept price
                    price = concept.price
                    charge_obj = None
                    
                    if item.get('charge_id'):
                        try:
                            charge_obj = Charge.objects.get(pk=item['charge_id'])
                            if charge_obj.is_paid:
                                raise Exception(f"La deuda '{charge_obj.concept.name}' ya se encuentra pagada.")
                                
                            price = charge_obj.amount # Use the amount from the charge
                            charge_obj.is_paid = True
                            charge_obj.save()
                        except Charge.DoesNotExist:
                            pass
                    
                    subtotal = price * qty
                    
                    # Calculate Taxes
                    if concept.iva_rate > 0:
                        base = subtotal 
                        iva = base * concept.iva_rate
                        total_15 += base
                        total_iva += iva
                    else:
                        total_0 += subtotal
                        
                    InvoiceDetail.objects.create(
                        invoice=invoice,
                        concept=concept,
                        quantity=qty,
                        unit_price=price,
                        subtotal=subtotal,
                        charge=charge_obj
                    )
                
                invoice.subtotal_0 = total_0
                invoice.subtotal_15 = total_15
                invoice.iva_total = total_iva
                invoice.total = total_0 + total_15 + total_iva
                invoice.save()
                
                # Register Payment
                Payment.objects.create(
                    invoice=invoice,
                    amount_paid=invoice.total,
                    verified=True
                )
                
                # Update Student Balance (Here we assume payment covers immediate debt or adds credit if previously owed)
                # Ideally, we should have a separate DEBT generation process.
                # For now, simplistic approach: Payment is an INCOME.
                # If we tracked debt, we would decrease debt.
                # Let's verify if account exists
                account, created = StudentAccount.objects.get_or_create(student=student, institution=student.institution or PaymentConcept.objects.first().institution)
                # account.balance -= invoice.total # If debt was positive
                # account.save()
                
                return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

            except Exception as e:
                import traceback
                traceback.print_exc()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        invoice = self.get_object()
        buffer = BytesIO()
        
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # --- HEADER (Institution Info) ---
        inst = invoice.institution
        
        # Logo placeholder (commented out as we handle file paths carefully)
        # if inst.logo:
        #     try:
        #         c.drawImage(inst.logo.path, 50, height - 100, width=100, preserveAspectRatio=True)
        #     except: pass

        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, inst.name)
        
        c.setFont("Helvetica", 9)
        c.drawString(50, height - 70, inst.address or "Dirección no registrada")
        c.drawString(50, height - 85, f"Tel: {inst.phone}  |  Email: {inst.email}")
        
        if hasattr(inst, 'obligado_contabilidad'):
            c.drawString(50, height - 100, f"Obligado a Llevar Contabilidad: {'SI' if inst.obligado_contabilidad else 'NO'}")
            
        if hasattr(inst, 'special_taxpayer_number') and inst.special_taxpayer_number:
            c.drawString(50, height - 115, f"Contribuyente Especial No: {inst.special_taxpayer_number}")

        # --- INVOICE BOX (RUC & Number) ---
        c.setLineWidth(1)
        c.rect(350, height - 130, 200, 100)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(360, height - 50, "R.U.C.: " + (inst.ruc if hasattr(inst, 'ruc') and inst.ruc else "9999999999999"))
        
        c.setFillColor(colors.white)
        c.rect(350, height - 80, 200, 25, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(360, height - 73, "F A C T U R A")
        
        c.setFont("Helvetica", 11)
        c.drawString(360, height - 100, f"No. {invoice.number}")
        
        # Authorization Info
        c.setFont("Helvetica", 8)
        c.drawString(360, height - 120, "AUTORIZACIÓN:")
        # Show real authorization status if available
        auth_status = invoice.sri_status if hasattr(invoice, 'sri_status') else 'PENDIENTE'
        auth_date = invoice.sri_authorization_date.strftime("%d/%m/%Y %H:%M") if hasattr(invoice, 'sri_authorization_date') and invoice.sri_authorization_date else 'PENDIENTE'
        
        c.drawString(360, height - 130, f"{auth_status} / {auth_date}") 

        # --- CLIENT INFO ---
        y_client = height - 160
        c.roundRect(40, y_client - 60, 515, 60, 5, stroke=1, fill=0)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_client - 15, f"Razón Social / Nombres y Apellidos:")
        c.setFont("Helvetica", 9)
        c.drawString(230, y_client - 15, invoice.client_name.upper())

        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_client - 30, f"Fecha Emisión:")
        c.setFont("Helvetica", 9)
        c.drawString(130, y_client - 30, invoice.issue_date.strftime("%d/%m/%Y"))

        c.setFont("Helvetica-Bold", 9)
        c.drawString(350, y_client - 30, f"RUC / CI:")
        c.setFont("Helvetica", 9)
        c.drawString(400, y_client - 30, invoice.client_ruc)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_client - 45, f"Dirección:")
        c.setFont("Helvetica", 9)
        c.drawString(110, y_client - 45, invoice.client_address[:80]) # Truncate if too long

        # --- DETAILS HEADER ---
        y_table = y_client - 90
        c.setFillColor(colors.lightgrey)
        c.rect(40, y_table, 515, 20, fill=1, stroke=1)
        c.setFillColor(colors.black)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_table + 6, "Cod.")
        c.drawString(90, y_table + 6, "Cant")
        c.drawString(130, y_table + 6, "Descripción")
        c.drawString(400, y_table + 6, "P. Unitario")
        c.drawString(480, y_table + 6, "Precio Total")
        
        # --- DETAILS ROWS ---
        y = y_table - 20
        c.setFont("Helvetica", 9)
        
        for detail in invoice.details.all():
            c.drawString(50, y, str(detail.concept.id))
            c.drawString(90, y, str(detail.quantity))
            c.drawString(130, y, detail.concept.name[:50])
            c.drawRightString(450, y, f"{detail.unit_price:.2f}")
            c.drawRightString(540, y, f"{detail.subtotal:.2f}")
            y -= 15
            
            # Page Break Check (Simple)
            if y < 100:
                c.showPage()
                y = height - 50

        # --- TOTALS ---
        y_totals = y - 20
        
        # Payment Method Box
        c.rect(40, y_totals - 60, 300, 60)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_totals - 15, "Forma de Pago")
        c.setFont("Helvetica", 9)
        pay_method_name = invoice.payment_method.name if invoice.payment_method else "Otros con Utilización del Sistema Financiero"
        c.drawString(50, y_totals - 30, pay_method_name)
        c.drawString(250, y_totals - 30, f"{invoice.total:.2f}")

        # Totals Box
        x_totals = 360
        w_totals = 195
        row_h = 15
        
        # Labels
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_totals + 5, y_totals - 15, "SUBTOTAL 15%")
        c.drawString(x_totals + 5, y_totals - 30, "SUBTOTAL 0%")
        c.drawString(x_totals + 5, y_totals - 45, "SUBTOTAL Sin Impuestos")
        c.drawString(x_totals + 5, y_totals - 60, "IVA 15%")
        c.drawString(x_totals + 5, y_totals - 75, "VALOR TOTAL")
        
        # Values
        c.setFont("Helvetica", 9)
        c.drawRightString(x_totals + w_totals - 5, y_totals - 15, f"{invoice.subtotal_15:.2f}")
        c.drawRightString(x_totals + w_totals - 5, y_totals - 30, f"{invoice.subtotal_0:.2f}")
        c.drawRightString(x_totals + w_totals - 5, y_totals - 45, f"{(invoice.subtotal_0 + invoice.subtotal_15):.2f}")
        c.drawRightString(x_totals + w_totals - 5, y_totals - 60, f"{invoice.iva_total:.2f}")
        
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(x_totals + w_totals - 5, y_totals - 75, f"{invoice.total:.2f}")
        
        # Grid for totals
        c.rect(x_totals, y_totals - 80, w_totals, 80)
        c.line(x_totals, y_totals - 20, x_totals + w_totals, y_totals - 20)
        c.line(x_totals, y_totals - 35, x_totals + w_totals, y_totals - 35)
        c.line(x_totals, y_totals - 50, x_totals + w_totals, y_totals - 50)
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Factura_{invoice.number}.pdf"'
        return response

    @action(detail=True, methods=['get'])
    def download_xml(self, request, pk=None):
        invoice = self.get_object()
        
        if not invoice.xml_content:
             return Response({'error': 'No existe XML generado para esta factura'}, status=status.HTTP_404_NOT_FOUND)

        buffer = BytesIO(invoice.xml_content.encode('utf-8'))
        response = HttpResponse(buffer, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="Factura_{invoice.number}.xml"'
        return response

    @action(detail=True, methods=['post'], url_path='send-sri')
    def send_sri(self, request, pk=None):
        """
        Envía la factura al SRI (Generar XML -> Firmar -> Enviar -> Autorizar).
        """
        invoice = self.get_object()
        
        if invoice.sri_status == 'AUTHORIZED':
            return Response({'message': 'Esta factura ya está autorizada.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Imports dinámicos
        try:
            from treasury.sri.xml_generator import InvoiceXmlBuilder
            from treasury.sri.signer import XadesSigner
            from treasury.sri.client import SriClient
            import os
        except ImportError as e:
            return Response({'error': f"Módulos SRI no instalados: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # 2. Generar XML
            builder = InvoiceXmlBuilder(invoice)
            access_key, xml_content = builder.build_xml()
            
            # Guardamos la clave si no existe
            invoice.access_key = access_key
            invoice.save()

            # 3. Firmar XML
            inst = invoice.institution
            if not inst.electronic_signature or not os.path.exists(inst.electronic_signature.path):
                return Response({'error': "La institución no tiene firma electrónica configurada (.p12)."}, status=status.HTTP_400_BAD_REQUEST)
            
            signed_xml = ""
            try:
                signer = XadesSigner(inst.electronic_signature.path, inst.signature_password)
                signed_xml = signer.sign_xml(xml_content)
                invoice.xml_content = signed_xml
                invoice.save()
            except Exception as e:
                return Response({'error': f"Error al firmar XML: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            # 4. Enviar al SRI (Recepción)
            # Determinar ambiente (1=Pruebas)
            urls = {
                'reception_test': inst.sri_url_reception_test,
                'authorization_test': inst.sri_url_authorization_test,
                'reception_prod': inst.sri_url_reception_prod,
                'authorization_prod': inst.sri_url_authorization_prod
            }
            client = SriClient(inst.sri_environment, urls=urls)
            
            success, msg, code = client.send_receipt(signed_xml)
            invoice.sri_status = code if code in ['PENDING', 'SENT', 'AUTHORIZED', 'REJECTED'] else 'SENT'
            invoice.sri_response = {'recepcion': msg}
            invoice.save()

            if not success and code != 'RECIBIDA': # RECIBIDA es el éxito
                 return Response({
                     'message': 'Error en Recepción SRI', 
                     'details': msg, 
                     'status': invoice.sri_status
                 }, status=status.HTTP_400_BAD_REQUEST)

            # 5. Solicitar Autorización (Inmediata)
            # Esperamos un momento? SRI a veces tarda millis/segundos. 
            import time
            time.sleep(2) 
            
            auth_success, auth_msg, auth_code, full_resp = client.request_authorization(access_key)
            
            invoice.sri_status = auth_code if auth_code in ['AUTHORIZED', 'REJECTED'] else invoice.sri_status
            
            # Merge responses
            current_resp = invoice.sri_response or {}
            current_resp['autorizacion'] = auth_msg
            current_resp['full_auth_xml'] = full_resp
            invoice.sri_response = current_resp
            
            if auth_code == 'AUTHORIZED':
                 invoice.sri_authorization_date = timezone.now() # Idealmente parsear del XML respuesta
                 invoice.save()
                 return Response({'message': 'Factura Autorizada por el SRI', 'status': 'AUTHORIZED'})
            else:
                 invoice.save()
                 return Response({'message': f'Factura Enviada pero no Autorizada: {auth_msg}', 'status': invoice.sri_status})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
