from django.db import models
from django.conf import settings
from .structure import Module

class Assignment(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    attachment = models.FileField(upload_to='learning/assignments/', null=True, blank=True)
    
    academic_category = models.ForeignKey(
        'academic.EvaluationCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lms_assignments',
        help_text="Categoría del sistema académico para sincronizar notas"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignment_submissions')
    file = models.FileField(upload_to='learning/submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Grading
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    teacher_feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"
