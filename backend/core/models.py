from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import UserManager

from core.thread_context import get_current_tenant_id

class TenantQuerySet(models.QuerySet):
    """
    QuerySet personalizado para aislamiento Multi-tenant.
    Provee métodos específicos para filtrar por contexto institucional.
    """
    def for_tenant(self, institution_id):
        if not institution_id:
            return self.none()
        return self.filter(institution_id=institution_id)

    def for_user(self, user):
        if user.is_superuser:
            return self.all()
        if not hasattr(user, 'institution') or not user.institution:
            return self.none()
        return self.filter(institution_id=user.institution_id)

class TenantManager(BaseUserManager, models.Manager):
    """
    Manager que obliga al aislamiento activo.
    get_queryset() filtra automáticamente basándose en el contexto del hilo (ThreadLocal).
    """
    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db)
        tenant_id = get_current_tenant_id()
        
        # Modo Seguro: Si hay un tenant en el hilo, filtramos.
        if tenant_id and tenant_id != 0:
            from django.db.models import Q
            # Si el modelo tiene campo is_superuser, incluir superusers globales para que no falle JWT Auth
            if hasattr(self.model, 'is_superuser'):
                return qs.filter(Q(institution_id=tenant_id) | Q(is_superuser=True))
            return qs.filter(institution_id=tenant_id)

        # Si NO hay tenant, no devolvemos registros por defecto
        return qs.none()

    def global_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def unscoped(self):
        return self.global_queryset()

    def get_by_natural_key(self, username):
        # Necesario para el sistema de autenticación de Django
        return self.get_queryset().get(**{self.model.USERNAME_FIELD: username})

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create and return a superuser with the given username, email and password.
        Validates that the supplied role is among the User model's Role choices.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'GLOBAL')
        # Validate role against User.Role TextChoices (if the model defines them)
        role_value = extra_fields.get('role')
        if hasattr(self.model, 'Role'):
            valid_roles = [choice.value for choice in self.model.Role]
            if role_value not in valid_roles:
                raise ValueError(f"Invalid role '{role_value}' for superuser. Valid roles: {valid_roles}")
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username, email=email, password=password, **extra_fields)

    def for_tenant(self, institution_id):
        return self.get_queryset().for_tenant(institution_id)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

class TenantModel(models.Model):
    """
    Modelo base abstracto para todas las entidades que pertenecen a una institución.
    Obliga a la presencia del campo 'institution' y usa el TenantManager.
    """
    institution = models.ForeignKey(
        'users.Institution', 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name="%(class)s_related"
    )
    is_orphaned = models.BooleanField(
        default=False, 
        help_text="Indica si el registro fue rescatado durante una migración de integridad por falta de relación padre."
    )
    
    objects = TenantManager()

    class Meta:
        abstract = True

class ActionLog(models.Model):
    """
    Modelo de auditoría centralizado para trazabilidad SaaS.
    Registra quién, cuándo y qué cambió en el sistema.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
        ('LOGIN', 'Inicio de Sesión'),
        ('LOGOUT', 'Cierre de Sesión'),
        ('SOFT_DELETE', 'Borrado Lógico'),
        ('RESTORE', 'Restauración'),
        ('SECURITY_ALERT', 'Alerta de Seguridad'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    institution = models.ForeignKey(
        'users.Institution', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    changes = models.JSONField(null=True, blank=True, help_text="Historial de cambios en formato JSON")
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Log de Auditoría")
        verbose_name_plural = _("Logs de Auditoría")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.model_name} ({self.timestamp})"
