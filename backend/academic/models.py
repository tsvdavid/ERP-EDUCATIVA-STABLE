from django.db import models
from users.models import Institution, User
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

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
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=50, blank=True) # e.g., "Primaria", "Secundaria"
    parallel = models.CharField(max_length=10, blank=True, default='A') # e.g., "A", "B"
    year = models.IntegerField() # Año lectivo
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('name', 'level', 'year', 'parallel', 'institution')

    def __str__(self):
        return f"{self.name} {self.parallel} ({self.year})"

class Subject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'TEACHER'}, related_name='subjects_taught')
    
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
        """
        Calculates averages for all subjects in the enrolled course.
        Returns a dictionary:
        {
            subject_id: {
                't1': float,
                't2': float,
                't3': float,
                'final': float
            }
        }
        """
        summary = {}
        subjects = self.course.subjects.all()
        grades = self.grades.all()
        
        # Pre-fetch categories for performance (though iterating loop is okay for low volume)
        # Better: iterate subjects
        # print("STARTING CALC FOR ENROLLMENT:", self.id, self.student.username)
        for subject in subjects:
            categories = subject.evaluation_categories.all()
            
            # Storage for details
            details = {1: [], 2: [], 3: []}
            scores = {1: 0.0, 2: 0.0, 3: 0.0}
            
            # Helper to calc trimester score
            def calc_trim(trim_num):
                 trim_cats = categories.filter(trimester=trim_num)
                 if not trim_cats.exists():
                     return 0.0
                 
                 total = 0.0
                 for cat in trim_cats:
                     # Find grade for this cat
                     g = next((g for g in grades if g.category_id == cat.id), None)
                     
                     grade_info = {
                         'category': cat.name,
                         'weight': float(cat.weight),
                         'score': float(g.score) if g else None,
                         'observation': g.observation if g else ""
                     }
                     details[trim_num].append(grade_info)

                     if g:
                         total += (float(g.score) * float(cat.weight)) / 100
                 return round(total, 2)

            scores[1] = calc_trim(1)
            scores[2] = calc_trim(2)
            scores[3] = calc_trim(3)
            
            final = round((scores[1] + scores[2] + scores[3]) / 3, 2)
            
            summary[subject.id] = {
                'name': subject.name,
                't1': scores[1],
                't2': scores[2],
                't3': scores[3],
                'final': final,
                'details': details # Returns {1: [...], 2: [...], 3: [...]}
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
    
    class Meta:
        verbose_name = "Categoría de Evaluación"
        verbose_name_plural = "Categorías de Evaluación"

    def __str__(self):
        return f"{self.name} ({self.weight}%) - {self.subject}"

class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='grades')
    # subject is technically redundant if we link to category -> subject, but good for quick lookup
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades') 
    category = models.ForeignKey(EvaluationCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='grades')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    # Deprecating eval_type in favor of category, keeping for backward compat if needed or just remove? 
    # User said "poder poner varior aportes", so string eval_type is weak. 
    # I'll keep it as optional description or specific task name (e.g. "Deber Pag 10" inside Category "Deberes")
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

    class Criticality(models.TextChoices):
        LOW = 'LOW', _('Baja (Informativa)')
        MEDIUM = 'MEDIUM', _('Media (Atención)')
        HIGH = 'HIGH', _('Alta (Acción Requerida)')

    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'}, related_name='observations')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'TEACHER'}, related_name='created_observations')
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.ACADEMIC)
    description = models.TextField()
    criticality = models.CharField(max_length=20, choices=Criticality.choices, default=Criticality.LOW)
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.student}: {self.criticality}"
