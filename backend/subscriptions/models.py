from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Institution
from datetime import timedelta
from django.utils import timezone

class Plan(models.Model):
    name = models.CharField(max_length=100)
    base_price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    base_price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    is_visible_for_sale = models.BooleanField(default=True)
    description = models.TextField(blank=True, default='')
    included_modules = models.ManyToManyField('Module', blank=True, related_name='included_in_plans')

    def __str__(self):
        return self.name

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Activo'),
        ('TRIAL_ACTIVE', 'Prueba Activa'),
        ('EXPIRING', 'Por Vencer'),
        ('GRACE', 'En Gracia'),
        ('SUSPENDED', 'Suspendido'),
        ('CANCELLED', 'Cancelado'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('MONTHLY', 'Mensual'),
        ('QUARTERLY', 'Trimestral'),
        ('SEMIANNUAL', 'Semestral'),
        ('YEARLY', 'Anual'),
    ]

    institution = models.OneToOneField(Institution, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    start_date = models.DateField()
    next_billing_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='MONTHLY')
    contract_duration_months = models.PositiveIntegerField(default=1)
    trial_duration_days = models.PositiveIntegerField(default=30)

    grace_until = models.DateField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution.name} - {self.status}"

    @property
    def days_remaining(self):
        if self.next_billing_date:
            from django.utils import timezone
            delta = self.next_billing_date - timezone.now().date()
            return max(0, delta.days)
        return 0

class GlobalSettings(models.Model):
    default_trial_days = models.PositiveIntegerField(default=30)
    grace_period_days = models.PositiveIntegerField(default=5)
    auto_suspend = models.BooleanField(default=True)
    reminder_days = models.JSONField(default=list) # [30, 15, 7, 3, 1]
    default_plan = models.ForeignKey('Plan', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_settings')
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración Global SaaS"
        verbose_name_plural = "Configuración Global SaaS"

    def __str__(self):
        return "Configuración Global SaaS"

class Module(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class SubscriptionModule(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='modules')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('subscription', 'module')
        
    def __str__(self):
        return f"{self.subscription.institution.name} - {self.module.name}"

class SubscriptionPayment(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Referencia de transferencia o detalles.")
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Pago de ${self.amount} - {self.subscription.institution.name}"

class SubscriptionAuditLog(models.Model):
    EVENT_TYPES = [
        ('PAYMENT_CONFIRMED', 'Pago Confirmado'),
        ('SUSPENDED', 'Cuenta Suspendida'),
        ('GRACE_ENTERED', 'Entró en Gracia'),
        ('EMAIL_SENT', 'Correo Enviado'),
        ('PAYMENT_ANOMALY', 'Anomalía de Pago'),
        ('FAILED_TASK', 'Tarea Fallida')
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        inst_name = self.institution.name if self.institution else 'Global'
        return f"[{self.event_type}] {inst_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class DailyKPI(models.Model):
    date = models.DateField(unique=True, default=timezone.now)
    mrr = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    active_customers = models.IntegerField(default=0)
    grace_count = models.IntegerField(default=0)
    suspended_count = models.IntegerField(default=0)
    payments_today = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"KPIs for {self.date}"
