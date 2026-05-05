from django.db import models
from core.models import TenantModel
from django.utils.translation import gettext_lazy as _
from cryptography.fernet import Fernet
from django.conf import settings
import base64

class EmailConfig(TenantModel):
    """Configuración SMTP por institución."""
    smtp_host = models.CharField(max_length=255)
    smtp_port = models.IntegerField(default=587)
    smtp_user = models.CharField(max_length=255)
    smtp_password_encrypted = models.TextField()
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    sender_name = models.CharField(max_length=255, help_text="Nombre que aparecerá en el envío")
    sender_email = models.CharField(max_length=255, help_text="Email que aparecerá como remitente")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Configuración de Email')
        verbose_name_plural = _('Configuraciones de Email')
        constraints = [
            models.UniqueConstraint(fields=['institution'], name='unique_email_config_per_tenant')
        ]

    def set_password(self, raw_password):
        # Usamos los primeros 32 bytes de la SECRET_KEY para Fernet (debe ser base64)
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].ljust(32, '0').encode())
        cipher_suite = Fernet(key)
        encrypted_text = cipher_suite.encrypt(raw_password.encode())
        self.smtp_password_encrypted = encrypted_text.decode()

    def get_password(self):
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].ljust(32, '0').encode())
        cipher_suite = Fernet(key)
        decrypted_text = cipher_suite.decrypt(self.smtp_password_encrypted.encode())
        return decrypted_text.decode()

    def __str__(self):
        return f"SMTP: {self.smtp_host} - {self.institution.name if self.institution else 'Global'}"

class EmailTemplate(TenantModel):
    """Plantillas de correo por institución."""
    CODE_CHOICES = [
        ('invoice_sent', _('Factura Enviada')),
        ('payment_reminder', _('Recordatorio de Pago')),
        ('grades_ready', _('Calificaciones Listas')),
        ('parent_notice', _('Aviso a Padres')),
        ('password_reset', _('Recuperar Contraseña')),
        ('welcome', _('Bienvenida')),
    ]
    code = models.CharField(max_length=50, choices=CODE_CHOICES)
    subject = models.CharField(max_length=255)
    html_body = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('institution', 'code')
        verbose_name = _('Plantilla de Email')
        verbose_name_plural = _('Plantillas de Email')

    def __str__(self):
        return f"{self.get_code_display()} - {self.institution.name if self.institution else 'Global'}"

class EmailLog(TenantModel):
    """Registro de correos enviados para auditoría y trazabilidad."""
    STATUS_CHOICES = [
        ('queued', _('En cola')),
        ('sent', _('Enviado')),
        ('failed', _('Fallido')),
    ]
    SEND_TYPE_CHOICES = [
        ('AUTO', _('Automático')),
        ('MANUAL', _('Manual')),
        ('REENVIO', _('Reenvío')),
        ('DESTINATARIO_ALTERNO', _('Destinatario Alterno')),
    ]
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    send_type = models.CharField(max_length=30, choices=SEND_TYPE_CHOICES, default='AUTO')
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    reference_id = models.CharField(max_length=100, blank=True, help_text="ID de referencia (ej: factura_id)")
    module_origin = models.CharField(max_length=50, blank=True, help_text="Módulo originador")

    class Meta:
        verbose_name = _('Log de Email')
        verbose_name_plural = _('Logs de Emails')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient} - {self.status} ({self.created_at})"
