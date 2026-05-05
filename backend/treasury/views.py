from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from io import BytesIO
import logging
import datetime
from .tasks import process_invoice_sri

logger = logging.getLogger(__name__)

from .serializers import (
    PaymentConceptSerializer, PaymentMethodSerializer, 
    InvoiceSerializer, CreateInvoiceSerializer, StudentAccountSerializer, ChargeSerializer,
    CreditNoteSerializer, DebitNoteSerializer, CustomerSerializer, EmailLogSerializer
)
from notifications.models import EmailLog
from .models import PaymentConcept, PaymentMethod, Invoice, InvoiceDetail, Payment, StudentAccount, Charge, CreditNote, DebitNote, Customer
from users.models import User, Institution
from users.tenant_mixins import InstitutionFilterMixin
from users.permissions import IsTreasuryStaff

class PaymentConceptViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = PaymentConcept.objects.filter(is_active=True)
    serializer_class = PaymentConceptSerializer
    permission_classes = [IsTreasuryStaff]
    tenant_field = 'institution'

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class PaymentMethodViewSet(InstitutionFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

class StudentAccountViewSet(InstitutionFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = StudentAccount.objects.all().select_related('student', 'student__institution')
    serializer_class = StudentAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = 'institution'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.role == 'STUDENT':
            return qs.filter(student=user).select_related('student', 'student__institution')
        elif user.role == 'PARENT':
            # Accounts of children
            children_ids = user.children.values_list('id', flat=True)
            return qs.filter(student__id__in=children_ids).select_related('student', 'student__institution')
        return qs

class CustomerViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsTreasuryStaff]
    tenant_field = 'institution'

    def get_queryset(self):
        qs = super().get_queryset()
        identification = self.request.query_params.get('identification')
        if identification:
            qs = qs.filter(identification=identification)
        
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search) | 
                Q(identification__icontains=search) |
                Q(business_name__icontains=search)
            )
        return qs

class ChargeViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = Charge.objects.all().select_related('student', 'concept', 'institution')
    serializer_class = ChargeSerializer
    tenant_field = 'institution'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'generate_monthly']:
            return [IsTreasuryStaff()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # Base optimization
        user = self.request.user
        queryset = super().get_queryset()
        
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
            
            try:
                from payments.models import Transaction
                verifying_txns = Transaction.objects.filter(status='VERIFYING').values_list('reference_id', flat=True)
                verifying_ids = [int(rid) for rid in verifying_txns if rid and rid.isdigit()]
                if verifying_ids:
                    queryset = queryset.exclude(id__in=verifying_ids)
            except Exception as e:
                pass
            
        return queryset

    @action(detail=False, methods=['post'], url_path='generate-monthly', permission_classes=[IsTreasuryStaff])
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
            concept = PaymentConcept.objects.get(pk=concept_id, institution=request.user.institution)
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

    @action(detail=False, methods=['get'], url_path='financial-stats', permission_classes=[IsTreasuryStaff])
    def financial_stats(self, request):
        """
        Summary of pending payments grouped by course.
        Supports filtering by academic_year_id and course_id.
        """
        user = self.request.user
        inst_id = user.institution_id
        if not inst_id:
             inst_id = request.headers.get('X-Institution-ID')
             
        if not inst_id:
             return Response({"error": "No institution context found"}, status=400)

        from django.db.models import Sum, Q
        from academic.models import Course
        
        year_id = request.query_params.get('academic_year_id')
        course_id = request.query_params.get('course_id')

        # Filter courses
        courses_query = Course.objects.filter(institution_id=inst_id)
        if year_id:
            try:
                from academic.models import AcademicYear
                ay = AcademicYear.objects.get(pk=year_id, institution_id=inst_id)
                courses_query = courses_query.filter(year=ay.year)
            except (AcademicYear.DoesNotExist, ValueError):
                pass
        if course_id:
            courses_query = courses_query.filter(id=course_id)

        # Global Total Pending
        global_filter = Q(student__institution_id=inst_id, is_paid=False)
        if year_id:
            try:
                from academic.models import AcademicYear
                ay = AcademicYear.objects.get(pk=year_id, institution_id=inst_id)
                global_filter &= Q(student__enrollments__course__year=ay.year)
            except (AcademicYear.DoesNotExist, ValueError):
                pass
        if course_id:
            global_filter &= Q(student__enrollments__course_id=course_id)
            
        global_total = Charge.objects.filter(global_filter).distinct().aggregate(total=Sum('amount'))['total'] or 0

        stats = []
        for course in courses_query:
            pending_total = Charge.objects.filter(
                student__enrollments__course=course,
                is_paid=False
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Count students with pending charges
            pending_count = Charge.objects.filter(
                student__enrollments__course=course,
                is_paid=False
            ).values('student').distinct().count()

            stats.append({
                'course_id': course.id,
                'course_name': f"{course.name} {course.parallel}",
                'pending_amount': float(pending_total),
                'pending_students': pending_count
            })
            
        return Response({
            'global_total': global_total,
            'by_course': stats
        })
            
        # Global Total
        global_pending = Charge.objects.filter(institution_id=inst_id, is_paid=False).aggregate(total=Sum('amount'))['total'] or 0
        total_debtors = Charge.objects.filter(institution_id=inst_id, is_paid=False).values('student').distinct().count()

        return Response({
            'by_course': stats,
            'global_total': float(global_pending),
            'total_debtors': total_debtors
        })

class InvoiceViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = Invoice.objects.all().select_related('institution', 'student', 'customer', 'payment_method').prefetch_related('details', 'details__concept')
    serializer_class = InvoiceSerializer
    tenant_field = 'institution'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'process_payment', 'commercial_dashboard']:
            return [IsTreasuryStaff()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().order_by('-id')

        if user.role in ['STUDENT', 'PARENT']:
             # Can only see own invoices
             if user.role == 'STUDENT':
                 return queryset.filter(student=user)
             else:
                 children_ids = user.children.values_list('id', flat=True)
                 return queryset.filter(student__id__in=children_ids)
        
        # Admin / Treasury: Allow filtering
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
            
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(customer__student_id=student_id)
            
        return queryset

    def perform_create(self, serializer):
        # HARDENING: Inyectar usuario y asegurar institución
        serializer.save(
            created_by=self.request.user,
            institution=self.request.user.institution
        )

    @action(detail=False, methods=['get'], url_path='commercial-dashboard')
    def commercial_dashboard(self, request):
        from django.db.models import Sum, Count
        inst_id = self.request.user.institution_id
        
        # Base filter for the institution
        base_qs = Invoice.objects.filter(institution_id=inst_id, status='ISSUED')
        
        # Total Sales
        total_sales = base_qs.aggregate(total=Sum('total'))['total'] or 0
        total_count = base_qs.count()
        
        # Sales by Customer Type
        by_type = base_qs.values('customer__customer_type').annotate(
            total=Sum('total'),
            count=Count('id')
        )
        
        # Formatting data
        stats = {
            'total_sales': float(total_sales),
            'total_count': total_count,
            'avg_ticket': float(total_sales / total_count) if total_count > 0 else 0,
            'by_type': {
                'STUDENT': 0,
                'INDIVIDUAL': 0,
                'COMPANY': 0,
                'WALKIN': 0
            },
            'counts_by_type': {
                'STUDENT': 0,
                'INDIVIDUAL': 0,
                'COMPANY': 0,
                'WALKIN': 0
            }
        }
        
        for item in by_type:
            c_type = item['customer__customer_type']
            if c_type in stats['by_type']:
                stats['by_type'][c_type] = float(item['total'])
                stats['counts_by_type'][c_type] = item['count']
                
        return Response(stats)

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
        
        customer_id = request.data.get('customer_id')
        if not customer_id:
            return Response({'error': 'customer_id es requerido'}, status=400)
            
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                # 1. Determine Customer with SECURITY FIX
                inst = request.user.institution
                if customer_id:
                    customer = Customer.objects.get(pk=customer_id, institution=inst)
                elif student_id:
                    # Legacy support/Auto-create if missing (though migration should have covered it)
                    student = User.objects.get(pk=student_id, institution=inst)
                    customer, _ = Customer.objects.get_or_create(
                        student=student,
                        institution=student.institution,
                        defaults={
                            'identification': student.cedula or '9999999999',
                            'first_name': student.first_name,
                            'last_name': student.last_name,
                            'address': student.address or 'Sin dirección',
                            'email': student.email or ''
                        }
                    )
                
                if not customer:
                    raise Exception("Se requiere un cliente válido para facturar.")

                pay_method_id = data.get('payment_method_id')
                pay_method = PaymentMethod.objects.get(pk=pay_method_id, institution=inst) if pay_method_id else None
                is_pending = request.data.get('is_pending', False)
                
                # Create Invoice Header (Transactional & Safe)
                from .utils import get_next_invoice_number
                inst = customer.institution
                est = getattr(inst, 'establishment_code', '001')
                pto = getattr(inst, 'emission_point', '001')
                
                invoice_number = get_next_invoice_number(inst, est, pto)
                
                invoice = Invoice.objects.create(
                    institution=inst,
                    customer=customer,
                    student=customer.student, # Set legacy field for compatibility
                    number=invoice_number,
                    status='ISSUED',
                    client_name=data.get('client_name', f"{customer.first_name} {customer.last_name}"),
                    client_ruc=data.get('client_ruc', customer.identification),
                    client_address=data.get('client_address') or customer.address or 'Sin dirección',
                    client_email=data.get('client_email') or customer.email or '',
                    payment_method=pay_method,
                    created_by=request.user
                )

                # UPDATE CUSTOMER PROFILE if new billing info is provided
                customer_updated = False
                new_address = data.get('client_address')
                new_email = data.get('client_email')
                
                if new_address and new_address != customer.address:
                    customer.address = new_address
                    customer_updated = True
                
                if new_email and new_email != customer.email:
                    customer.email = new_email
                    customer_updated = True

                if customer_updated:
                    customer.save()

                total_0 = 0
                total_15 = 0
                total_iva = 0
                
                # Create Details
                for item in data['concepts']:
                    concept = PaymentConcept.objects.get(pk=item['concept_id'], institution=inst)
                    qty = item.get('quantity', 1)
                    
                    # Determine price: from charge if exists (snapshot) or current concept price
                    price = concept.price
                    charge_obj = None
                    
                    if item.get('charge_id'):
                        try:
                            charge_obj = Charge.objects.get(pk=item['charge_id'], institution=inst)
                            if charge_obj.is_paid:
                                raise Exception(f"La deuda '{charge_obj.concept.name}' ya se encuentra pagada.")
                                
                            price = charge_obj.amount # Use the amount from the charge
                            if not is_pending:
                                charge_obj.is_paid = True
                                charge_obj.save()
                        except Charge.DoesNotExist:
                            pass
                        # Create temporary debt if needed
                        if is_pending:
                            from datetime import date
                            charge_obj = Charge.objects.create(
                                institution=customer.institution,
                                customer=customer,
                                student=customer.student,
                                concept=concept,
                                amount=price * qty,
                                due_date=date.today(),
                                is_paid=False
                            )
                    
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
                        institution=inst,
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
                
                # Trigger SRI Process automatically
                process_invoice_sri.delay(invoice.id)

                
                # Register Payment if not pending
                if not is_pending:
                    Payment.objects.create(
                        institution=inst,
                        invoice=invoice,
                        amount_paid=invoice.total,
                        verified=True
                    )
                
                # Update Student Balance (Here we assume payment covers immediate debt or adds credit if previously owed)
                # Ideally, we should have a separate DEBT generation process.
                # For now, simplistic approach: Payment is an INCOME.
                # If we tracked debt, we would decrease debt.
                # Update Balance (Only if it's a student)
                if customer.student:
                    account, created = StudentAccount.objects.get_or_create(student=customer.student, institution=customer.institution)
                    # account.balance -= invoice.total 
                    # account.save()
                
                response_data = InvoiceSerializer(invoice).data
                return Response(response_data, status=status.HTTP_201_CREATED)

            except Exception as e:
                import traceback
                traceback.print_exc()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='mass-billing')
    @transaction.atomic
    def mass_billing(self, request):
        """
        Receives:
        {
            "student_ids": [1, 2, 3],
            "payment_method_id": 2, // optional
            "concept_id": 1
        }
        """
        student_ids = request.data.get('student_ids', [])
        concept_id = request.data.get('concept_id')
        pay_method_id = request.data.get('payment_method_id')
        
        if not student_ids or not concept_id:
            return Response({'error': 'Faltan datos requeridos (student_ids, concept_id)'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            concept = PaymentConcept.objects.get(pk=concept_id)
            pay_method = PaymentMethod.objects.get(pk=pay_method_id) if pay_method_id else None
            
            students = User.objects.filter(id__in=student_ids, role='STUDENT')
            if not students.exists():
                return Response({'error': 'No se encontraron estudiantes para facturar.'}, status=status.HTTP_400_BAD_REQUEST)
                
            from .utils import get_next_invoice_number
            inst = students.first().institution or concept.institution
            est = getattr(inst, 'establishment_code', '001')
            pto = getattr(inst, 'emission_point', '001')
            
            from datetime import date
            created_count = 0
            
            for student in students:
                invoice_number = get_next_invoice_number(inst, est, pto)
                
                # 0. Obtener o crear perfil de cliente para el estudiante
                customer, _ = Customer.objects.get_or_create(
                    student=student,
                    institution=inst,
                    defaults={
                        'identification': student.cedula or f"NI-{student.id}",
                        'first_name': student.first_name,
                        'last_name': student.last_name,
                        'email': student.email or '',
                        'address': student.address or 'Sin dirección'
                    }
                )

                # 1. Crear Deuda (Charge) ya que es pendiente (is_pending=True equivalent)
                charge_obj = Charge.objects.create(
                    institution=inst,
                    customer=customer,
                    student=student,
                    concept=concept,
                    amount=concept.price,
                    due_date=date.today(),
                    is_paid=False
                )
                
                # 2. Crear Factura
                invoice = Invoice.objects.create(
                    institution=inst,
                    customer=customer,
                    student=student,
                    number=invoice_number,
                    status='ISSUED',
                    client_name=f"{student.first_name} {student.last_name}",
                    client_ruc=student.cedula or '9999999999999',
                    client_address=student.address or 'Sin dirección',
                    client_email=student.email or '',
                    payment_method=pay_method,
                    created_by=request.user
                )
                
                # 3. Detalles y Totales
                subtotal = concept.price
                total_15 = 0
                total_0 = 0
                iva = 0
                
                if concept.iva_rate > 0:
                    total_15 = subtotal
                    iva = subtotal * concept.iva_rate
                else:
                    total_0 = subtotal
                    
                InvoiceDetail.objects.create(
                    invoice=invoice,
                    concept=concept,
                    quantity=1,
                    unit_price=concept.price,
                    subtotal=subtotal,
                    charge=charge_obj
                )
                
                invoice.subtotal_0 = total_0
                invoice.subtotal_15 = total_15
                invoice.iva_total = iva
                invoice.total = total_0 + total_15 + iva
                invoice.save()
                
                # Trigger SRI Process automatically
                process_invoice_sri.delay(invoice.id)

                
                # No se crea el 'Payment' log porque es pendiente.
                created_count += 1
                
            return Response({
                'message': f'Facturación masiva de {created_count} facturas pendientes con éxito.',
                'count': created_count
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        invoice = self.get_object()
        try:
            from treasury.utils import generate_invoice_pdf
            pdf_bytes = generate_invoice_pdf(invoice)
            from django.http import HttpResponse
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Factura_{invoice.number}.pdf"'
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['get'])
    def download_xml(self, request, pk=None):
        invoice = self.get_object()
        
        if not invoice.xml_content:
             return Response({'error': 'No existe XML generado para esta factura'}, status=status.HTTP_404_NOT_FOUND)

        buffer = BytesIO(invoice.xml_content.encode('utf-8'))
        response = HttpResponse(buffer, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="Factura_{invoice.number}.xml"'
        return response

    @action(detail=True, methods=['post'], url_path='send-email', permission_classes=[IsTreasuryStaff])
    def send_email(self, request, pk=None):
        """
        Envío manual/reenvío de la factura al correo registrado.
        Soporta parámetro 'sync=true' para administradores en caso de emergencia.
        """
        invoice = self.get_object()
        is_sync = request.query_params.get('sync') == 'true' and request.user.role in ['ADMIN', 'LOCAL_ADMIN']
        
        # 1. Validación Previa de Email
        if not invoice.client_email:
            return Response({'error': 'El cliente no tiene un correo electrónico registrado. Por favor, actualice los datos del cliente antes de enviar.'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Validación de estado SRI
        if invoice.sri_status != 'AUTHORIZED' and invoice.status != 'ISSUED':
             return Response({'error': 'Solo se pueden enviar correos de facturas emitidas o autorizadas.'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Rate Limiting (Máximo 5 reenvíos por hora)
        one_hour_ago = timezone.now() - datetime.timedelta(hours=1)
        recent_logs_count = EmailLog.objects.filter(
            institution=invoice.institution,
            reference_id=str(invoice.id),
            module_origin='treasury.invoice',
            created_at__gte=one_hour_ago
        ).exclude(send_type='AUTO').count()

        if recent_logs_count >= 5:
            return Response({'error': 'Se ha superado el límite de 5 reenvíos por hora para esta factura.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 4. Determinar tipo de envío
        has_been_sent = EmailLog.objects.filter(institution=invoice.institution, reference_id=str(invoice.id), module_origin='treasury.invoice', status='sent').exists()
        send_type = 'REENVIO' if has_been_sent else 'MANUAL'

        try:
            from notifications.tasks import send_invoice_email_task
            if is_sync:
                # Envío síncrono controlado (Fallback manual)
                success = send_invoice_email_task(
                    invoice_id=invoice.id, 
                    sent_by_id=request.user.id, 
                    send_type=send_type
                )
                if success:
                    return Response({'message': f'Correo ({send_type}) enviado exitosamente (Sincrónico).'})
                else:
                    return Response({'error': 'El envío síncrono falló. Verifique la configuración SMTP.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Envío asíncrono estándar
                send_invoice_email_task.delay(
                    invoice_id=invoice.id, 
                    sent_by_id=request.user.id, 
                    send_type=send_type
                )
                return Response({'message': f'Correo ({send_type}) encolado con éxito.'})
        except Exception as e:
            logger.error(f"Error triggering invoice email: {str(e)}")
            return Response({'error': f"Error al procesar el envío: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='send-to-alt-email', permission_classes=[IsTreasuryStaff])
    def send_to_alt_email(self, request, pk=None):
        """
        Envío de la factura a un correo alternativo proporcionado por el usuario.
        """
        invoice = self.get_object()
        alt_email = request.data.get('email')

        if not alt_email:
            return Response({'error': 'Se requiere un correo electrónico destinatario.'}, status=status.HTTP_400_BAD_REQUEST)

        # Rate Limiting
        one_hour_ago = timezone.now() - datetime.timedelta(hours=1)
        recent_logs_count = EmailLog.objects.filter(
            institution=invoice.institution,
            reference_id=str(invoice.id),
            module_origin='treasury.invoice',
            created_at__gte=one_hour_ago
        ).exclude(send_type='AUTO').count()

        if recent_logs_count >= 5:
            return Response({'error': 'Límite de reenvíos excedido para esta factura.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            from notifications.tasks import send_invoice_email_task
            send_invoice_email_task.delay(
                invoice_id=invoice.id, 
                recipient=alt_email,
                sent_by_id=request.user.id, 
                send_type='DESTINATARIO_ALTERNO'
            )
            return Response({'message': 'Correo alternativo encolado con éxito.'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='email-history', permission_classes=[IsTreasuryStaff])
    def email_history(self, request, pk=None):
        """
        Consulta el historial de correos enviados para esta factura usando la relación directa y los logs.
        """
        invoice = self.get_object()
        
        logs = EmailLog.objects.filter(
            institution=invoice.institution,
            reference_id=str(invoice.id),
            module_origin='treasury.invoice'
        ).order_by('-created_at')
        
        serializer = EmailLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='sri-monitoring')
    def sri_monitoring(self, request):
        """
        Operational dashboard metrics and list.
        """
        from django.db.models import Count, Q
        from django.utils import timezone
        import datetime
        
        inst_id = self.request.user.institution_id
        today = timezone.now().date()
        
        # 1. Metrics
        metrics = Invoice.objects.filter(institution_id=inst_id).aggregate(
            pending_sri=Count('id', filter=Q(sri_status='DRAFT')),
            retry_queue=Count('id', filter=Q(sri_status='PENDING_SRI')),
            authorized_today=Count('id', filter=Q(sri_status='AUTHORIZED', sri_authorization_date__date=today)),
            rejected_today=Count('id', filter=Q(sri_status='REJECTED', updated_at__date=today))
        )
        
        # 2. Latest SRI Invoices (Filterable by status)
        status_filter = request.query_params.get('status')
        qs = Invoice.objects.filter(institution_id=inst_id).exclude(sri_status='DRAFT').order_by('-id')
        
        if status_filter:
            qs = qs.filter(sri_status=status_filter)
            
        # Optimization: Only select needed fields
        # Note: 'institution' is needed for TenantModel logic usually, but here we are in a ViewSet with institution context
        invoices = qs[:50]
        
        # Format data
        invoice_list = []
        for inv in invoices:
            last_resp = "-"
            if inv.sri_response:
                reception = inv.sri_response.get('reception', {})
                auth = inv.sri_response.get('authorization', {})
                last_resp = auth.get('msg') or reception.get('msg') or "-"
                messages = auth.get('messages') or reception.get('messages') or []
                
            invoice_list.append({
                'id': inv.id,
                'number': inv.number,
                'client_name': inv.client_name,
                'status': inv.sri_status,
                'attempts': inv.sri_attempts,
                'last_response': last_resp,
                'messages': messages,
                'access_key': inv.access_key,
                'updated_at': inv.updated_at
            })
            
        return Response({
            'metrics': metrics,
            'invoices': invoice_list
        })

    @action(detail=True, methods=['post'], url_path='preflight-check')
    def preflight_check(self, request, pk=None):
        """
        Realiza una validación estructural y de firma antes de enviar al SRI.
        """
        invoice = self.get_object()
        from .sri.xml_generator import InvoiceXmlBuilder
        from .sri.signer import XadesSigner
        
        try:
            # 1. Generar XML
            builder = InvoiceXmlBuilder(invoice)
            access_key, xml_str = builder.build_xml()
            
            # 2. Intentar Firmar (si hay firma)
            inst = invoice.institution
            if not inst.sri_p12_file or not inst.sri_p12_password:
                return Response({'error': 'No se ha configurado firma electrónica para esta institución.'}, status=400)
            
            signer = XadesSigner(inst.sri_p12_file.path, inst.sri_p12_password)
            signed_xml = signer.sign_xml(xml_str)
            
            # 3. Validación básica estructural
            from lxml import etree
            etree.fromstring(signed_xml.encode('utf-8'))
            
            return Response({
                'valid': True,
                'message': 'Validación estructural y firma exitosa.',
                'access_key': access_key
            })
        except Exception as e:
            return Response({
                'valid': False,
                'error': str(e)
            }, status=400)

    @action(detail=True, methods=['post'], url_path='send-sri')
    def send_sri(self, request, pk=None):
        """
        Inicia el proceso asíncrono de envío al SRI.
        """
        invoice = self.get_object()
        
        if invoice.sri_status == 'AUTHORIZED':
            return Response({'error': 'Esta factura ya está autorizada.'}, status=status.HTTP_400_BAD_REQUEST)

        # Reset status if it was rejected to allow retry
        if invoice.sri_status == 'REJECTED':
            invoice.sri_status = 'DRAFT'
            invoice.save()

        try:
            from .tasks import process_invoice_sri
            process_invoice_sri.delay(invoice.id)
            return Response({
                'message': 'Proceso de facturación electrónica iniciado en segundo plano.',
                'status': invoice.sri_status
            })
        except Exception as e:
            return Response({'error': f"Error al encolar tarea: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreditNoteViewSet(InstitutionFilterMixin, viewsets.ModelViewSet):
    queryset = CreditNote.objects.all().select_related('invoice')
    serializer_class = CreditNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    tenant_lookup = 'invoice__institution'

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.role in ['STUDENT', 'PARENT']:
            if user.role == 'STUDENT':
                return queryset.filter(invoice__student=user)
            else:
                children_ids = user.children.values_list('id', flat=True)
                return queryset.filter(invoice__student__id__in=children_ids)
        return queryset

    def perform_create(self, serializer):
        # HARDENING: Filtrar por institución del usuario para evitar fugas de secuencia
        inst = self.request.user.institution
        last_note = CreditNote.objects.filter(invoice__institution=inst).order_by('-id').first()
        seq = (last_note.id + 1) if last_note else 1
        number = f"NC-{str(seq).zfill(6)}"
        serializer.save(number=number)

class DebitNoteViewSet(viewsets.ModelViewSet):
    queryset = DebitNote.objects.all().select_related('invoice')
    serializer_class = DebitNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.role in ['STUDENT', 'PARENT']:
            if user.role == 'STUDENT':
                return queryset.filter(invoice__student=user)
            else:
                children_ids = user.children.values_list('id', flat=True)
                return queryset.filter(invoice__student__id__in=children_ids)
        return queryset

    def perform_create(self, serializer):
        # HARDENING: Filtrar por institución del usuario para evitar fugas de secuencia
        inst = self.request.user.institution
        last_note = DebitNote.objects.filter(invoice__institution=inst).order_by('-id').first()
        seq = (last_note.id + 1) if last_note else 1
        number = f"ND-{str(seq).zfill(6)}"
        serializer.save(number=number)
