from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import ProcedureTemplate, StudentRequest
from .serializers import ProcedureTemplateSerializer, StudentRequestSerializer, StudentRequestActionSerializer
from django.db import transaction

import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from django.core.files.base import ContentFile

class ProcedureTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = ProcedureTemplateSerializer
    permission_classes = [permissions.IsAuthenticated] # Needs custom for writers vs readers
    
    def get_queryset(self):
        user = self.request.user
        qs = ProcedureTemplate.objects.filter(institution=user.institution, is_active=True)
        return qs
        
    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)


class StudentRequestViewSet(viewsets.ModelViewSet):
    serializer_class = StudentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        qs = StudentRequest.objects.filter(institution=user.institution).order_by('-request_date')
        
        # Students see only theirs
        if user.role == 'STUDENT':
            return qs.filter(student=user)
        # Parents see their children's
        if user.role == 'PARENT':
            children_ids = user.children.values_list('id', flat=True)
            return qs.filter(student__id__in=children_ids)
            
        # Teachers and Admins can see requests assigned to their role
        return qs

    def perform_create(self, serializer):
        serializer.save(
            institution=self.request.user.institution,
            student=self.request.user  # The student making the request
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser]) # Update this based on your roles later
    def resolve(self, request, pk=None):
        """
        Admins/Rectors/Teachers use this to approve or reject a request.
        """
        student_request = self.get_object()
        serializer = StudentRequestActionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        action_type = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        if student_request.status != 'PENDING':
            return Response({"error": "La solicitud ya fue procesada."}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            if action_type == 'REJECT':
                student_request.status = 'REJECTED'
                student_request.response_notes = notes
                student_request.approved_by = request.user
                student_request.approval_date = timezone.now()
                student_request.save()
                return Response({'status': 'Rechazado'})
                
            elif action_type == 'APPROVE':
                student_request.status = 'APPROVED'
                student_request.response_notes = notes
                student_request.approved_by = request.user
                student_request.approval_date = timezone.now()
                
                # Generate PDF Document based on Template
                template_text = student_request.template.content_template
                
                # Replace dynamic variables
                student = student_request.student
                course_name = "N/A"
                # If you have an academic dependency to find the current course:
                from academic.models import Enrollment, AcademicYear
                active_year = AcademicYear.objects.filter(institution=student.institution, is_active=True).first()
                if active_year:
                    enrollment = Enrollment.objects.filter(student=student, course__year=active_year.year).first()
                    if enrollment:
                        course_name = f"{enrollment.course.name} '{enrollment.course.parallel}'"
                
                replacements = {
                    '{{student_name}}': f"{student.first_name} {student.last_name}",
                    '{{student_cedula}}': student.cedula or 'No registrada',
                    '{{course_name}}': course_name,
                    '{{date}}': timezone.now().strftime("%d/%m/%Y"),
                    '{{institution_name}}': student.institution.name,
                }
                
                for key, val in replacements.items():
                    template_text = template_text.replace(key, str(val))
                
                # Build the PDF using platypus for text wrapping
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
                styles = getSampleStyleSheet()
                
                elements = []
                
                # Title
                title_style = styles['Heading1']
                title_style.alignment = 1 # Center
                elements.append(Paragraph(student_request.template.name.upper(), title_style))
                elements.append(Spacer(1, 24))
                
                # Content
                body_style = styles['Normal']
                body_style.fontName = 'Helvetica'
                body_style.fontSize = 12
                body_style.leading = 14
                
                # Handle line breaks in the template
                paragraphs = template_text.split('\n')
                for p in paragraphs:
                    if p.strip():
                        elements.append(Paragraph(p, body_style))
                        elements.append(Spacer(1, 12))
                
                # Footer / Signatures
                elements.append(Spacer(1, 48))
                elements.append(Paragraph("___________________________", body_style))
                elements.append(Paragraph(f"Autorizado por: {request.user.first_name} {request.user.last_name}", body_style))
                elements.append(Paragraph(f"Fecha: {timezone.now().strftime('%d/%m/%Y')}", body_style))
                
                doc.build(elements)
                
                pdf_bytes = buffer.getvalue()
                buffer.close()
                
                # Attach to FileField
                file_name = f"Solicitud_{student_request.id}_{timezone.now().timestamp()}.pdf"
                student_request.generated_file.save(file_name, ContentFile(pdf_bytes))
                
                student_request.save()
                return Response({'status': 'Aprobado y Documento Generado', 'file_url': student_request.generated_file.url})
