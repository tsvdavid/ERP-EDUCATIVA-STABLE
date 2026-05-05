from django.db import models
from users.models import User, Institution
from core.models import TenantModel
from django.utils import timezone

class PolicyVersion(TenantModel):
    """
    Versions of Privacy Policies.
    Supports granular consent (e.g., separating Marketing from Essential Terms).
    """
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    name = models.CharField(max_length=100) # e.g. "Términos y Condiciones", "Política de Cookies"
    version = models.CharField(max_length=20) # e.g. "1.0", "2.1"
    content = models.TextField()
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} v{self.version}"

class ConsentRecord(TenantModel):
    """
    Immutable record of user consent.
    """
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consents')
    policy = models.ForeignKey(PolicyVersion, on_delete=models.PROTECT)
    accepted = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        status = "Accepted" if self.accepted else "Rejected"
        return f"{self.user.username} - {self.policy} - {status}"

class TreatmentActivity(TenantModel):
    """
    Registro de Actividades de Tratamiento (RAT).
    Inventory of personal data processing activities.
    """
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    name = models.CharField(max_length=200) # e.g. "Gestión de Nómina"
    purpose = models.TextField() # Finalidad
    legal_basis = models.CharField(max_length=100) # Base de Legitimación
    data_categories = models.TextField() # Qué datos se tratan
    retention_period = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class ARCORequest(TenantModel):
    """
    Solicitudes de Derechos ARCO (Acceso, Rectificación, Cancelación, Oposición).
    """
    RIGHT_CHOICES = (
        ('ACCESS', 'Acceso'),
        ('RECTIFICATION', 'Rectificación'),
        ('CANCELLATION', 'Cancelación / Supresión'),
        ('OPPOSITION', 'Oposición'),
        ('PORTABILITY', 'Portabilidad'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pendiente'),
        ('IN_REVIEW', 'En Revisión Legal'),
        ('APPROVED', 'Aprobado'),
        ('REJECTED', 'Rechazado'),
        ('EXECUTED', 'Ejecutado'),
    )

    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    requester = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    right_type = models.CharField(max_length=20, choices=RIGHT_CHOICES)
    details = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    response_content = models.TextField(blank=True, help_text="Legal response to the user")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateField(help_text="Legal deadline to respond (usually 15 days)")
    
    # Executed steps
    anonymization_performed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.deadline:
            # Ecuador LOPDP usually gives 15 days for Access/Rectification
            self.deadline = timezone.now().date() + timezone.timedelta(days=15)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_right_type_display()} - {self.requester.username}"

class DataBreach(TenantModel):
    """
    Registro de Incidentes de Seguridad.
    """
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    title = models.CharField(max_length=200)
    description = models.TextField()
    detected_at = models.DateTimeField()
    severity = models.CharField(max_length=20, choices=[('LOW', 'Baja'), ('MEDIUM', 'Media'), ('HIGH', 'Alta'), ('CRITICAL', 'Crítica')])
    
    affected_users = models.ManyToManyField(User, blank=True)
    is_reported_to_authority = models.BooleanField(default=False)
    report_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BREACH: {self.title} ({self.detected_at})"
