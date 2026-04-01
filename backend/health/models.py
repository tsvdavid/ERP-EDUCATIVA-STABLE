from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User, Institution


# ===== FICHAS PERMANENTES (NO se resetean por año) =====

class MedicalRecord(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='medical_record')
    blood_type = models.CharField(max_length=10, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    chronic_conditions = models.TextField(blank=True, null=True)
    regular_medication = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _("Ficha Médica")
        verbose_name_plural = _("Fichas Médicas")

    def __str__(self):
        return f"Ficha Médica: {self.student.get_full_name()}"


class DeceRecord(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dece_record')
    family_context = models.TextField(blank=True, null=True)
    academic_history = models.TextField(blank=True, null=True)
    special_educational_needs = models.BooleanField(default=False)
    sen_details = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Ficha DECE")
        verbose_name_plural = _("Fichas DECE")

    def __str__(self):
        return f"Ficha DECE: {self.student.get_full_name()}"


# ===== CONSULTAS / VISITAS (vinculadas a año lectivo) =====

class MedicalVisit(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_visits')
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='doctor_visits')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE, related_name='medical_visits', null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    symptoms = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    treatment = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Consulta Médica")
        verbose_name_plural = _("Consultas Médicas")
        ordering = ['-date']

    def __str__(self):
        return f"Consulta: {self.student.get_full_name()} ({self.date.strftime('%Y-%m-%d')})"


class DeceVisit(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dece_visits')
    counselor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dece_interventions')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE, related_name='dece_visits', null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    observations = models.TextField(blank=True, null=True)
    agreements = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Intervención DECE")
        verbose_name_plural = _("Intervenciones DECE")
        ordering = ['-date']

    def __str__(self):
        return f"Intervención: {self.student.get_full_name()} ({self.date.strftime('%Y-%m-%d')})"


# ===== SEGUIMIENTO CONDUCTUAL (vinculado a año lectivo) =====

class BehaviorRecord(models.Model):
    class RecordType(models.TextChoices):
        POSITIVE = 'POSITIVE', _('Positiva')
        NEGATIVE_MILD = 'NEGATIVE_MILD', _('Negativa Leve')
        NEGATIVE_SEVERE = 'NEGATIVE_SEVERE', _('Negativa Grave')
        ACADEMIC = 'ACADEMIC', _('Académica')
        SOCIOEMOTIONAL = 'SOCIOEMOTIONAL', _('Socioemocional')

    class TemplateType(models.TextChoices):
        PARTICIPATES = 'PARTICIPATES', _('Participa activamente')
        DOES_NOT_SUBMIT = 'DOES_NOT_SUBMIT', _('No entrega tareas')
        DISRUPTS_CLASS = 'DISRUPTS_CLASS', _('Interrumpe clase')
        FIGHTS = 'FIGHTS', _('Pelea / agresión')
        BULLYING = 'BULLYING', _('Acoso escolar')
        TARDINESS = 'TARDINESS', _('Llegada tardía reiterada')
        GOOD_BEHAVIOR = 'GOOD_BEHAVIOR', _('Buen comportamiento')
        HELPS_PEERS = 'HELPS_PEERS', _('Ayuda a compañeros')
        OTHER = 'OTHER', _('Otro (personalizado)')

    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'}, related_name='behavior_records')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_behavior_records')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE, related_name='behavior_records')
    record_type = models.CharField(max_length=30, choices=RecordType.choices)
    template = models.CharField(max_length=30, choices=TemplateType.choices, default=TemplateType.OTHER)
    description = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    subject = models.ForeignKey('academic.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='behavior_records')
    course = models.ForeignKey('academic.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='behavior_records')
    triggered_alert = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Registro Conductual")
        verbose_name_plural = _("Registros Conductuales")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_record_type_display()} - {self.student.get_full_name()} ({self.date})"


class BehaviorCase(models.Model):
    class AreaDestino(models.TextChoices):
        DECE = 'DECE', _('DECE')
        MEDICAL = 'MEDICAL', _('Dispensario Médico')
        EXTERNAL = 'EXTERNAL', _('Institución Externa')

    class CaseStatus(models.TextChoices):
        OPEN = 'OPEN', _('Abierto')
        IN_PROGRESS = 'IN_PROGRESS', _('En Seguimiento')
        CLOSED = 'CLOSED', _('Cerrado')

    class CasePriority(models.TextChoices):
        LOW = 'LOW', _('Baja')
        MEDIUM = 'MEDIUM', _('Media')
        HIGH = 'HIGH', _('Alta')
        CRITICAL = 'CRITICAL', _('Crítica')

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behavior_cases')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE, related_name='behavior_cases')
    area = models.CharField(max_length=20, choices=AreaDestino.choices)
    status = models.CharField(max_length=20, choices=CaseStatus.choices, default=CaseStatus.OPEN)
    priority = models.CharField(max_length=20, choices=CasePriority.choices, default=CasePriority.MEDIUM)
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cases')
    parent_case = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='derived_cases')
    derived_from_area = models.CharField(max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    behavior_records = models.ManyToManyField(BehaviorRecord, blank=True, related_name='related_cases')

    class Meta:
        verbose_name = _("Caso Conductual")
        verbose_name_plural = _("Casos Conductuales")
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_area_display()}] {self.title} - {self.student.get_full_name()}"


class CaseFollowUp(models.Model):
    class FollowUpType(models.TextChoices):
        INTERVIEW_STUDENT = 'INTERVIEW_STUDENT', _('Entrevista con Estudiante')
        INTERVIEW_PARENT = 'INTERVIEW_PARENT', _('Entrevista con Representante')
        OBSERVATION = 'OBSERVATION', _('Observación')
        AGREEMENT = 'AGREEMENT', _('Acuerdo/Compromiso')
        REFERRAL = 'REFERRAL', _('Derivación')
        NOTE = 'NOTE', _('Nota Interna')

    case = models.ForeignKey(BehaviorCase, on_delete=models.CASCADE, related_name='follow_ups')
    follow_up_type = models.CharField(max_length=30, choices=FollowUpType.choices)
    content = models.TextField()
    agreements = models.TextField(blank=True, default='')
    is_confidential = models.BooleanField(default=False, help_text=_("Solo visible para DECE/Médico"))
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    attachment = models.FileField(upload_to='cases/attachments/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Seguimiento de Caso")
        verbose_name_plural = _("Seguimientos de Caso")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_follow_up_type_display()} - Caso #{self.case_id}"


class StudentRiskProfile(models.Model):
    class RiskLevel(models.TextChoices):
        GREEN = 'GREEN', _('Bien')
        YELLOW = 'YELLOW', _('Riesgo')
        RED = 'RED', _('Crítico')

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risk_profiles')
    academic_year = models.ForeignKey('academic.AcademicYear', on_delete=models.CASCADE, related_name='risk_profiles')
    behavior_score = models.FloatField(default=100.0)
    attendance_score = models.FloatField(default=100.0)
    academic_score = models.FloatField(default=100.0)
    overall_risk = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.GREEN)
    last_calculated = models.DateTimeField(auto_now=True)
    negative_count_7d = models.IntegerField(default=0)
    has_open_case = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'academic_year')
        verbose_name = _("Perfil de Riesgo")
        verbose_name_plural = _("Perfiles de Riesgo")

    def __str__(self):
        return f"{self.get_overall_risk_display()} {self.student.get_full_name()}"


class AlertRule(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='alert_rules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    negative_count_threshold = models.IntegerField(default=3)
    days_window = models.IntegerField(default=7)
    include_low_grades = models.BooleanField(default=False)
    grade_threshold = models.FloatField(default=5.0)
    include_absences = models.BooleanField(default=False)
    absence_threshold = models.IntegerField(default=5)
    auto_create_case = models.BooleanField(default=True)
    target_area = models.CharField(max_length=20, choices=BehaviorCase.AreaDestino.choices, default='DECE')
    notify_dece = models.BooleanField(default=True)
    notify_tutor = models.BooleanField(default=True)
    notify_parents = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Regla de Alerta")
        verbose_name_plural = _("Reglas de Alerta")

    def __str__(self):
        return f"{self.name} ({self.institution.name})"
