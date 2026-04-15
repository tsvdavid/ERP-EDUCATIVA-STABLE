from django.db import models
from users.models import Institution, User
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

def get_qualitative_grade(score, scale_type='QUALITATIVE_DESTREZAS'):
    if score is None:
        return "-"
    try:
        val = float(score)
    except (ValueError, TypeError):
        return "-"
        
    if scale_type == 'QUALITATIVE_PROYECTOS':
        if val >= 9.0: return "EX"
        elif val >= 7.0: return "MB"
        elif val >= 5.0: return "B"
        else: return "R"
    elif scale_type == 'QUALITATIVE_COMPORTAMIENTO':
        if val >= 9.0: return "A"
        elif val >= 7.0: return "B"
        elif val >= 5.0: return "C"
        elif val >= 4.0: return "D"
        else: return "E"
    else:
        # Default Destrezas
        if val >= 9.0: return "DA"
        elif val >= 7.0: return "EP"
        elif val >= 5.0: return "I"
        else: return "NE"

class AcademicYear(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='academic_years')
    name = models.CharField(max_length=100)  # e.g., "2024-2025"
    year = models.IntegerField(help_text="Identificador numérico del año")  # To link with Course.year
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False, help_text="Establecer como año activo actual")
    is_closed = models.BooleanField(default=False, help_text="Si está cerrado, no se permiten cambios globalmente")

    class Meta:
        unique_together = ('institution', 'year')
        verbose_name = _("Año Lectivo")
        verbose_name_plural = _("Años Lectivos")

    def __str__(self):
        return f"{self.name} ({self.institution})"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Ensure only one active year per institution
            AcademicYear.objects.filter(institution=self.institution, is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class AcademicPeriod(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='periods')
    number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        choices=[(1, 'Trimestre 1'), (2, 'Trimestre 2'), (3, 'Trimestre 3')]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False, help_text="Bloquea la calificación para este periodo")

    class Meta:
        unique_together = ('academic_year', 'number')
        ordering = ['number']
        verbose_name = _("Periodo Académico")
        verbose_name_plural = _("Periodos Académicos")

    def __str__(self):
        return f"Trimestre {self.number} - {self.academic_year.name}"

class Course(models.Model):
    class GradingType(models.TextChoices):
        QUANTITATIVE = 'QUANTITATIVE', _('Cuantitativa (0-10)')
        QUALITATIVE_DESTREZAS = 'QUALITATIVE_DESTREZAS', _('Cualitativa - Destrezas (DA, EP, I, NE)')
        QUALITATIVE_PROYECTOS = 'QUALITATIVE_PROYECTOS', _('Cualitativa - Proyectos (EX, MB, B, R)')
        QUALITATIVE_COMPORTAMIENTO = 'QUALITATIVE_COMPORTAMIENTO', _('Cualitativa - Comportamiento (A, B, C, D, E)')

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=50, blank=True) # e.g., "Primaria", "Secundaria"
    parallel = models.CharField(max_length=10, blank=True, default='A') # e.g., "A", "B"
    year = models.IntegerField() # Año lectivo
    grading_type = models.CharField(max_length=50, choices=GradingType.choices, default=GradingType.QUANTITATIVE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('name', 'level', 'year', 'parallel', 'institution')

    def __str__(self):
        return f"{self.name} {self.parallel} ({self.year})"

class Subject(models.Model):
    class SubjectGradingType(models.TextChoices):
        INHERIT = 'INHERIT', _('Heredar del Curso')
        QUANTITATIVE = 'QUANTITATIVE', _('Cuantitativa (0-10)')
        QUALITATIVE_DESTREZAS = 'QUALITATIVE_DESTREZAS', _('Cualitativa - Destrezas (DA, EP, I, NE)')
        QUALITATIVE_PROYECTOS = 'QUALITATIVE_PROYECTOS', _('Cualitativa - Proyectos (EX, MB, B, R)')
        QUALITATIVE_COMPORTAMIENTO = 'QUALITATIVE_COMPORTAMIENTO', _('Cualitativa - Comportamiento (A, B, C, D, E)')

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'TEACHER'}, related_name='subjects_taught')
    grading_type = models.CharField(max_length=30, choices=SubjectGradingType.choices, default=SubjectGradingType.INHERIT)
    
    def __str__(self):
        return f"{self.name} - {self.course}"

    class Meta:
        unique_together = ('course', 'name')
        verbose_name = _("Materia")
        verbose_name_plural = _("Materias")

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'}, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    date_enrolled = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} -> {self.course}"

    def calculate_averages(self):
        summary = {}
        subjects = self.course.subjects.all()
        grades = self.grades.all()
        
        for subject in subjects:
            categories = subject.evaluation_categories.all()
            details = {1: [], 2: [], 3: []}
            scores = {1: 0.0, 2: 0.0, 3: 0.0}
            
            def calc_trim(trim_num):
                 # Root categories for this trimester
                 main_cats = [c for c in categories if c.trimester == trim_num] # and c.parent_category_id is None]
                 
                 if not main_cats:
                     return 0.0
                 
                 total = 0.0
                 for cat in main_cats:
                     children = []
                     
                     if children:
                         cat_score = 0.0
                         for child in children:
                             g_child = next((g for g in grades if g.category_id == child.id), None)
                             if g_child:
                                 cat_score += (float(g_child.score) * float(child.weight)) / 100
                         score_val = cat_score
                         g_obs = ""
                     else:
                         g = next((g for g in grades if g.category_id == cat.id), None)
                         score_val = float(g.score) if g else None
                         g_obs = g.observation if g else ""
                     
                     grade_info = {
                         'category': cat.name,
                         'weight': float(cat.weight),
                         'score': score_val,
                         'observation': g_obs,
                         'has_children': len(children) > 0
                     }
                     details[trim_num].append(grade_info)

                     if score_val is not None:
                         total += (score_val * float(cat.weight)) / 100
                 return round(total, 2)

            scores[1] = calc_trim(1)
            scores[2] = calc_trim(2)
            scores[3] = calc_trim(3)
            
            final = round((scores[1] + scores[2] + scores[3]) / 3, 2)
            
            effective_grading_type = subject.grading_type
            if effective_grading_type == 'INHERIT':
                effective_grading_type = self.course.grading_type
                
            qualitative_string = get_qualitative_grade(final, effective_grading_type) if effective_grading_type != 'QUANTITATIVE' else "-"
            
            summary[subject.id] = {
                'name': subject.name,
                't1': scores[1],
                't2': scores[2],
                't3': scores[3],
                'final': final,
                'effective_grading_type': effective_grading_type,
                'qualitative': qualitative_string,
                'details': details 
            }
            
        return summary

class EvaluationCategory(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='evaluation_categories')
    name = models.CharField(max_length=100) # e.g., "Parcial 1", "Deberes"
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=100.00) # Percentage link 30.00
    trimester = models.PositiveSmallIntegerField(
        choices=[(1, 'Trimestre 1'), (2, 'Trimestre 2'), (3, 'Trimestre 3')], 
        default=1
    )
    # parent_category = models.ForeignKey('self', null=True, blank=True, related_name='subcategories', on_delete=models.CASCADE, help_text="Dejar en blanco si es categoría principal. Si se selecciona, este aporte será sub-aporte de dicha categoría.")
    
    class Meta:
        verbose_name = "Categoría de Evaluación"
        verbose_name_plural = "Categorías de Evaluación"

    def __str__(self):
        return f"{self.name} ({self.weight}%) - {self.subject}"

class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades') 
    category = models.ForeignKey(EvaluationCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='grades')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.CharField(max_length=200, blank=True) 
    date = models.DateField()
    observation = models.TextField(blank=True)

    def __str__(self):
        return f"{self.enrollment.student} - {self.subject}: {self.score}"

class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', _('Presente')
        ABSENT = 'ABSENT', _('Ausente')
        LATE = 'LATE', _('Tarde')
        EXCUSED = 'EXCUSED', _('Justificado')

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('enrollment', 'date')

class Observation(models.Model):
    class Type(models.TextChoices):
        BEHAVIORAL = 'BEHAVIORAL', _('Conductual')
        ACADEMIC = 'ACADEMIC', _('Académica')
        POSITIVE = 'POSITIVE', _('Positiva')
        SOCIOEMOTIONAL = 'SOCIOEMOTIONAL', _('Socioemocional')
        MEDICAL = 'MEDICAL', _('Médica / Salud')

    class Criticality(models.TextChoices):
        LOW = 'LOW', _('Baja (Informativa)')
        MEDIUM = 'MEDIUM', _('Media (Atención)')
        HIGH = 'HIGH', _('Alta (Acción Requerida)')

    class Department(models.TextChoices):
        TEACHER = 'TEACHER', _('Docente / General')
        DECE = 'DECE', _('DECE (Consejería)')
        MEDICAL = 'MEDICO', _('Médico / Dispensario')

    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'}, related_name='observations')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'TEACHER'}, related_name='created_observations')
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.ACADEMIC)
    description = models.TextField()
    criticality = models.CharField(max_length=20, choices=Criticality.choices, default=Criticality.LOW)
    date = models.DateField(auto_now_add=True)
    
    # New Fields for Institutional Tracking
    is_private = models.BooleanField(
        default=False, 
        help_text="Si es privada, solo personal del DECE, Médicos y Administradores podrán verla."
    )
    referred_to = models.CharField(
        max_length=20, 
        choices=Department.choices, 
        default=Department.TEACHER,
        help_text="Departamento al que se deriva o pertenece este registro"
    )
    resolution = models.TextField(blank=True, help_text="Resolución o seguimiento dado por el departamento encargado")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.student}: {self.criticality}"

class ClassSchedule(models.Model):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 1, _('Lunes')
        TUESDAY = 2, _('Martes')
        WEDNESDAY = 3, _('Miércoles')
        THURSDAY = 4, _('Jueves')
        FRIDAY = 5, _('Viernes')
        SATURDAY = 6, _('Sábado')
        SUNDAY = 7, _('Domingo')

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name = _('Horario de Clase')
        verbose_name_plural = _('Horarios de Clases')
        unique_together = ('subject', 'day_of_week', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.subject} - {self.get_day_of_week_display()} ({self.start_time.strftime('%H:%M')} a {self.end_time.strftime('%H:%M')})"
