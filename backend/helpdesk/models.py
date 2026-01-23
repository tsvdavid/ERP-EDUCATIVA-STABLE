from django.db import models
from users.models import User, Institution
from django.utils import timezone

class ServiceCatalog(models.Model):
    """
    Catalog of services available for tickets.
    e.g. "Hardware Support", "Access Request", "Software Installation"
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories', verbose_name="Categoría Padre")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sla_hours = models.PositiveIntegerField(default=24, help_text="Time to resolve in hours")
    
    def __str__(self):
        return self.name

class Workflow(models.Model):
    """
    Defines the lifecycle of a ticket.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class PassStep(models.Model):
    """
    Steps/Levels within a workflow.
    """
    STEP_TYPES = (
        ('APPROVAL', 'Aprobación'),
        ('EXECUTION', 'Ejecución'),
        ('AUTOMATION', 'Automatización'),
    )
    
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=100)
    step_type = models.CharField(max_length=20, choices=STEP_TYPES, default='EXECUTION')
    order = models.PositiveIntegerField(default=1)
    
    # Configuration for Approvals
    approver_role = models.CharField(max_length=50, blank=True, help_text="Role required to approve")
    
    def __str__(self):
        return f"{self.workflow.name} - Step {self.order}: {self.name}"

class Ticket(models.Model):
    PRIORITY_CHOICES = (
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'Crítica'),
    )
    
    STATUS_CHOICES = (
        ('OPEN', 'Abierto'),
        ('IN_PROGRESS', 'En Progreso'),
        ('PENDING_APPROVAL', 'Pendiente Aprobación'),
        ('RESOLVED', 'Resuelto'),
        ('CLOSED', 'Cerrado'),
        ('REOPENED', 'Reabierto'),
    )

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, db_index=True)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_tickets', db_index=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', db_index=True)
    
    category = models.ForeignKey(ServiceCatalog, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    current_step = models.ForeignKey(PassStep, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Reopening logic
    reopen_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"#{self.id} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.due_date and self.category:
            # Simple SLA calc (not checking business hours yet)
            self.due_date = timezone.now() + timezone.timedelta(hours=self.category.sla_hours)
        super().save(*args, **kwargs)

class TicketSurvey(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='survey')
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ScheduledJob(models.Model):
    """
    Orchestrator for recurring tickets (Preventive Maintenance).
    """
    FREQUENCY_CHOICES = (
        ('DAILY', 'Diario'),
        ('WEEKLY', 'Semanal'),
        ('MONTHLY', 'Mensual'),
    )

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # Template for the ticket to be created
    ticket_category = models.ForeignKey(ServiceCatalog, on_delete=models.PROTECT)
    ticket_title = models.CharField(max_length=200)
    ticket_description = models.TextField()
    ticket_priority = models.CharField(max_length=10, choices=Ticket.PRIORITY_CHOICES, default='MEDIUM')
    
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Job: {self.name} ({self.frequency})"

class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.author} on #{self.ticket.id}"

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    file = models.FileField(upload_to='helpdesk/attachments/')
    filename = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.file and not self.filename:
            self.filename = self.file.name
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.filename
