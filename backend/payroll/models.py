from django.db import models
from core.models import TenantModel
from users.models import User, Institution
from django.utils.translation import gettext_lazy as _

class Department(TenantModel):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ('institution', 'code')
        verbose_name = _('Departamento')

    def __str__(self):
        return f"{self.name} ({self.institution.name})"

class Position(TenantModel):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='positions')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = _('Cargo')

    def __str__(self):
        return self.name

class Employee(TenantModel):
    GENDER_CHOICES = (('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro'))
    
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='employees')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    
    identification = models.CharField(max_length=20)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('institution', 'identification')
        verbose_name = _('Empleado')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.identification}"

class WorkShift(TenantModel):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='work_shifts')
    name = models.CharField(max_length=50) # e.g. "Administrativo Mañana"
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_minutes = models.PositiveIntegerField(default=5)
    
    class Meta:
        verbose_name = _('Jornada Laboral')

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"

class Contract(TenantModel):
    CONTRACT_TYPES = (
        ('INDEFINIDO', 'Indefinido'),
        ('EVENTUAL', 'Eventual'),
        ('POR_OBRA', 'Por obra/servicio'),
        ('PASANTIA', 'Pasantía'),
    )
    
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='contracts')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='contracts')
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    shift = models.ForeignKey(WorkShift, on_delete=models.PROTECT)
    
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES, default='INDEFINIDO')
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Contrato')

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.position.name}"

class Attendance(TenantModel):
    STATUS_CHOICES = (
        ('NORMAL', 'Normal'),
        ('LATE', 'Atraso'),
        ('ABSENT', 'Falta'),
        ('PERMISSION', 'Permiso/Justificado'),
    )
    
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='attendances')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NORMAL')
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        verbose_name = _('Asistencia')

class PayrollPeriod(TenantModel):
    STATE_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('APPROVED', 'Aprobado'), # Triggers Accounting Signal
        ('PAID', 'Pagado'),
    )
    
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='payroll_periods')
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='DRAFT')
    
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_payrolls')

    class Meta:
        unique_together = ('institution', 'year', 'month')
        verbose_name = _('Periodo de Nómina')

    def __str__(self):
        import calendar
        return f"Nómina {calendar.month_name[self.month]} {self.year}"

class PayrollRoll(TenantModel):
    """
    Individual payroll record for an employee in a period.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='payroll_rolls')
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='rolls')
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    overtime_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    bonus_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    iess_personal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # 9.45%
    loan_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Provisiones Legales Ecuador
    provision_13th = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    provision_14th = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    provision_reserve_funds = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    iess_patronal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    net_to_pay = models.DecimalField(max_digits=12, decimal_places=2)
    company_cost = models.DecimalField(max_digits=12, decimal_places=2) # Incl. Provisiones

    class Meta:
        unique_together = ('period', 'employee')
        verbose_name = _('Rol de Pagos Individual')

class PayrollItem(TenantModel):
    TYPE_CHOICES = (('EARNING', 'Ingreso'), ('DEDUCTION', 'Descuento'))
    
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='payroll_items')
    roll = models.ForeignKey(PayrollRoll, on_delete=models.CASCADE, related_name='details')
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    name = models.CharField(max_length=100) # e.g. "Horas Extra 50%", "Aporte IESS"
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _('Detalle de Nómina')
