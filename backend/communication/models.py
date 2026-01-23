from django.db import models
from users.models import User
from django.utils.translation import gettext_lazy as _

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Threading support (Simple parent-child relationship)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    attachment = models.FileField(upload_to='messages/attachments/', null=True, blank=True)

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.subject}"

    class Meta:
        ordering = ['-created_at']

class Notification(models.Model):
    class Type(models.TextChoices):
        ALERT = 'ALERT', _('Alerta')
        NOTICE = 'NOTICE', _('Aviso')
        EVENT = 'EVENT', _('Evento')
        MESSAGE = 'MESSAGE', _('Mensaje')

    class Priority(models.TextChoices):
        HIGH = 'HIGH', _('Alta')
        MEDIUM = 'MEDIUM', _('Media')
        LOW = 'LOW', _('Baja')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.NOTICE)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Metadata opcional para relacionar con otros objetos (ej: ID de la falta o nota)
    related_object_id = models.IntegerField(null=True, blank=True)
    related_content_type = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.type} for {self.user}: {self.title}"

    class Meta:
        ordering = ['-created_at']

class Notice(models.Model):
    """Avisos generales (Tablón de Anuncios)"""
    class TargetRole(models.TextChoices):
        ALL = 'ALL', _('Todos')
        PARENTS = 'PARENT', _('Padres')
        TEACHERS = 'TEACHER', _('Profesores')
        STUDENTS = 'STUDENT', _('Estudiantes')

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_notices')
    title = models.CharField(max_length=255)
    content = models.TextField()
    target_role = models.CharField(max_length=20, choices=TargetRole.choices, default=TargetRole.ALL)
    
    # New granular targeting
    target_course = models.ForeignKey('academic.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='notices')
    target_students = models.ManyToManyField(User, blank=True, related_name='specific_notices', limit_choices_to={'role': 'STUDENT'})
    
    event_date = models.DateTimeField(null=True, blank=True)
    event_end_date = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='notices/attachments/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Holiday(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    description = models.TextField(blank=True)
    # If we want per-institution holidays later, add ForeignKey to Institution
    # For now, global or managed by Admin is fine.
    # To support "custom" vs "system", maybe a type?
    is_system = models.BooleanField(default=False) # True if from holidays lib

    class Meta:
        ordering = ['date']
        unique_together = ('date', 'name')

    def __str__(self):
        return f"{self.date}: {self.name}"
