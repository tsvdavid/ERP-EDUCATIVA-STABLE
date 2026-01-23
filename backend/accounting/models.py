from django.db import models
from users.models import Institution, User
from django.core.exceptions import ValidationError

class FiscalYear(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='fiscal_years')
    year = models.PositiveIntegerField()
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('institution', 'year')

    def __str__(self):
        return f"{self.year} - {self.institution.name}"

class Account(models.Model):
    ACCOUNT_TYPES = (
        ('ASSET', 'Activo'),
        ('LIABILITY', 'Pasivo'),
        ('EQUITY', 'Patrimonio'),
        ('INCOME', 'Ingresos'),
        ('EXPENSE', 'Gastos'),
    )

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='accounts')
    code = models.CharField(max_length=50) # e.g. 1.1.01
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.PositiveIntegerField(default=1) # 1=Group, 2=Subgroup, etc.
    
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    
    # SRI Related
    tax_id = models.CharField(max_length=20, blank=True, verbose_name="Casillero SRI")

    class Meta:
        ordering = ['code']
        unique_together = ('institution', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        # Calculate level based on parent
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)

class JournalEntry(models.Model):
    STATE_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('POSTED', 'Asentado'),
        ('CANCELLED', 'Anulado'),
    )

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='journal_entries')
    date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True) # e.g. "Factura #001"
    
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='DRAFT')
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Asiento #{self.id} - {self.date} - {self.description[:30]}"

    @property
    def total_debit(self):
        return sum(item.debit for item in self.items.all())

    @property
    def total_credit(self):
        return sum(item.credit for item in self.items.all())

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit

class JournalItem(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='items')
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    
    description = models.CharField(max_length=200, blank=True)
    
    debit = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.account.code} | D:{self.debit} C:{self.credit}"

    def clean(self):
        if self.debit > 0 and self.credit > 0:
             raise ValidationError("A journal item cannot have both debit and credit.")

class AccountingConfig(models.Model):
    KEYS = (
        ('ASSET_CASH', 'Activo - Caja (Efectivo)'),
        ('ASSET_BANK', 'Activo - Bancos (Transferencia)'),
        ('ASSET_CXC', 'Activo - Cuentas por Cobrar Clientes'),
        ('LIABILITY_IVA', 'Pasivo - IVA Cobrado'),
        ('INCOME_SERVICES', 'Ingresos - Servicios Educativos'),
        ('LIABILITY_SUPPLIERS', 'Pasivo - Proveedores (Cuentas por Pagar)'),
        ('ASSET_TAX_CREDIT', 'Activo - IVA Crédito Tributario'),
    )

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='accounting_configs')
    key = models.CharField(max_length=50, choices=KEYS)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('institution', 'key')
        verbose_name = "Configuración Contable"
        verbose_name_plural = "Configuraciones Contables"

    def __str__(self):
        return f"{self.institution.name} : {self.get_key_display()} -> {self.account.code}"
