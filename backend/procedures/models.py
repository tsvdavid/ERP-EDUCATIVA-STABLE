from django.db import models
from users.models import User, Institution

class ProcedureTemplate(models.Model):
    """
    Template for a document request, e.g. "Certificado de Matrícula", "Permiso Médico".
    """
    ROLE_CHOICES = (
        ('RECTOR', 'Rector'),
        ('TEACHER', 'Profesor'),
        ('ADMIN', 'Administrativo'),
        ('LOCAL_ADMIN', 'Administrador Local'),
    )

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='procedure_templates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Instrucciones para el estudiante.")
    content_template = models.TextField(help_text="Texto base del documento con variables {{student_name}}, {{course_name}}, etc.")
    
    requires_approval = models.BooleanField(default=True, help_text="Si es Falso, se aprueba y genera automáticamente.")
    approver_role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='ADMIN', help_text="Rol requerido para aprobar esta solicitud.")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.institution.name}"


class StudentRequest(models.Model):
    """
    A specific request made by a student based on a template.
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pendiente'),
        ('APPROVED', 'Aprobado'),
        ('REJECTED', 'Rechazado'),
    )

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='student_requests')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='procedures_requested', limit_choices_to={'role': 'STUDENT'})
    template = models.ForeignKey(ProcedureTemplate, on_delete=models.CASCADE, related_name='requests')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    details = models.TextField(blank=True, help_text="Motivo o justificación llenada por el estudiante.")
    
    request_date = models.DateTimeField(auto_now_add=True)
    
    # Approval fields
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='procedures_approved')
    approval_date = models.DateTimeField(null=True, blank=True)
    response_notes = models.TextField(blank=True, help_text="Comentarios del aprobador (ej. motivo de rechazo).")
    
    # The generated PDF file
    generated_file = models.FileField(upload_to='procedures/generated/', null=True, blank=True)

    def __str__(self):
        return f"Request: {self.template.name} by {self.student.username} ({self.status})"
