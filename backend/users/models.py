from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class Institution(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='institutions/logos/', blank=True, null=True)
    
    # SRI Fields
    ruc = models.CharField(max_length=13, blank=True, verbose_name="RUC")
    establishment_code = models.CharField(max_length=3, default='001', verbose_name="Cod. Establecimiento")
    emission_point = models.CharField(max_length=3, default='001', verbose_name="Punto Emision")
    obligado_contabilidad = models.BooleanField(default=False, verbose_name="Obligado a llevar contabilidad")
    
    # SRI Electronic Invoicing
    ENVIRONMENT_CHOICES = [
        (1, 'Pruebas'),
        (2, 'Producción')
    ]
    sri_environment = models.IntegerField(choices=ENVIRONMENT_CHOICES, default=1, verbose_name="Ambiente SRI")
    electronic_signature = models.FileField(upload_to='institutions/signatures/', blank=True, null=True, verbose_name="Firma Electrónica (.p12)")
    signature_password = models.CharField(max_length=255, blank=True, verbose_name="Contraseña Firma")
    special_taxpayer_number = models.CharField(max_length=13, blank=True, verbose_name="Nro. Contribuyente Especial")
    
    # SRI URLs (Configurable)
    sri_url_reception_test = models.URLField(default="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline", verbose_name="URL Recepción (Pruebas)")
    sri_url_authorization_test = models.URLField(default="https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline", verbose_name="URL Autorización (Pruebas)")
    sri_url_reception_prod = models.URLField(default="https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline", verbose_name="URL Recepción (Producción)")
    sri_url_authorization_prod = models.URLField(default="https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline", verbose_name="URL Autorización (Producción)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrador')
        LOCAL_ADMIN = 'LOCAL_ADMIN', _('Administrador Local')
        ACCOUNTANT = 'ACCOUNTANT', _('Auditor Contable')
        RECTOR = 'RECTOR', _('Rector/Supervisor')
        TEACHER = 'TEACHER', _('Profesor')
        DECE = 'DECE', _('Consejero DECE')
        MEDICO = 'MEDICO', _('Médico Dispensario')
        PARENT = 'PARENT', _('Padre/Representante')
        STUDENT = 'STUDENT', _('Estudiante')

    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE, 
        related_name='users',
        null=True, 
        blank=True
    )
    # Relación Padre -> Hijos (Estudiantes)
    children = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='parents',
        limit_choices_to={'role': 'STUDENT'}
    )

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.STUDENT
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Masculino'), ('F', 'Femenino')],
        blank=True,
        default=''
    )

    # New Fields
    second_name = models.CharField(max_length=150, blank=True, default='')
    second_surname = models.CharField(max_length=150, blank=True, default='')
    cedula = models.CharField(max_length=20, null=True, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # New Demographics & Professional Info
    nationality = models.CharField(max_length=50, blank=True, default='Ecuatoriana')
    civil_status = models.CharField(
        max_length=20,
        choices=[('SOLTERO', 'Soltero/a'), ('CASADO', 'Casado/a'), ('DIVORCIADO', 'Divorciado/a'), ('VIUDO', 'Viudo/a'), ('UNION_LIBRE', 'Unión Libre')],
        blank=True,
        default=''
    )
    titles = models.TextField(blank=True, default='', help_text="Títulos profesionales y masterados")
    teaching_category = models.CharField(
        max_length=2,
        choices=[('A', 'Categoría A'), ('B', 'Categoría B'), ('C', 'Categoría C'), ('D', 'Categoría D'), ('E', 'Categoría E'), ('F', 'Categoría F'), ('G', 'Categoría G'), ('H', 'Categoría H'), ('I', 'Categoría I'), ('J', 'Categoría J')],
        blank=True,
        default=''
    )

    # Campos de contacto (Re-activados para coincidir con la base de datos)
    representative_name = models.CharField(max_length=255, blank=True, default='')
    representative_cedula = models.CharField(max_length=20, blank=True, default='')
    representative_email = models.EmailField(blank=True, default='')
    representative_address = models.TextField(blank=True, default='')
    use_representative_for_billing = models.BooleanField(default=False)
    secondary_phone = models.CharField(max_length=20, blank=True, default='')
    
    # Evitar conflictos con auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('grupos'),
        blank=True,
        help_text=_(
            'Los grupos a los que pertenece este usuario. Un usuario obtendrá todos los permisos '
            'otorgados a cada uno de sus grupos.'
        ),
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('permisos de usuario'),
        blank=True,
        help_text=_('Permisos específicos para este usuario.'),
        related_name="custom_user_set",
        related_query_name="user",
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'cedula'], name='unique_cedula_per_institution'),
            # Note: Username is unique by default in AbstractUser. 
            # We can't easily change that without custom auth backend.
            # But we can enforce email uniqueness per institution if needed.
        ]
