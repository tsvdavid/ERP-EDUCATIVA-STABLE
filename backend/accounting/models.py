from django.db import models
from users.models import Institution, User
from django.core.exceptions import ValidationError
from core.models import TenantModel

class FiscalYear(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    year = models.PositiveIntegerField()
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('institution', 'year')

    def __str__(self):
        return f"{self.year} - {self.institution.name}"

class MonthlyClose(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    is_closed = models.BooleanField(default=True)
    closed_at = models.DateTimeField(auto_now_add=True)
    closed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='monthly_closures')

    class Meta:
        unique_together = ('institution', 'year', 'month')
        ordering = ['-year', '-month']

    def __str__(self):
        import calendar
        return f"{calendar.month_name[self.month]} {self.year} - {self.institution.name} ({'Cerrado' if self.is_closed else 'Abierto'})"

class Account(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    ACCOUNT_TYPES = (
        ('ASSET', 'Activo'),
        ('LIABILITY', 'Pasivo'),
        ('EQUITY', 'Patrimonio'),
        ('INCOME', 'Ingresos'),
        ('EXPENSE', 'Gastos'),
    )

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

class JournalEntry(TenantModel):
    STATE_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('POSTED', 'Asentado'),
        ('CANCELLED', 'Anulado'),
    )

    ENTRY_TYPES = (
        ('REGULAR', 'Regular'),
        ('ADJUSTMENT', 'Ajuste de Integridad'),
    )

    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True) # e.g. "Factura #001"
    
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='DRAFT')
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='REGULAR')
    is_unbalanced = models.BooleanField(default=False, help_text="Marcado automático para asientos que no cumplen el balance Debe == Haber.")
    adjustment_for = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='adjustments', help_text="Enlace al asiento original que este registro está corrigiendo.")
    
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

class JournalItem(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
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
        
        if self.journal_entry and self.institution != self.journal_entry.institution:
             raise ValidationError(f"Multi-tenant Violation: JournalItem institution ({self.institution}) must match JournalEntry institution ({self.journal_entry.institution})")

class AccountingConfig(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    KEYS = (
        ('ASSET_CASH', 'Activo - Caja (Efectivo)'),
        ('ASSET_BANK', 'Activo - Bancos (Transferencia)'),
        ('ASSET_CXC', 'Activo - Cuentas por Cobrar Clientes'),
        ('LIABILITY_IVA', 'Pasivo - IVA Cobrado'),
        ('INCOME_SERVICES', 'Ingresos - Servicios Educativos'),
        ('LIABILITY_SUPPLIERS', 'Pasivo - Proveedores (Cuentas por Pagar)'),
        ('ASSET_TAX_CREDIT', 'Activo - IVA Crédito Tributario'),
        ('EQUITY_RETAINED_EARNINGS', 'Patrimonio - Resultados Acumulados / Utilidad del Ejercicio'),
        ('EXPENSE_DISCOUNTS', 'Gastos - Descuentos Concedidos'),
        ('EXPENSE_SALARIES', 'Gastos - Sueldos y Salarios'),
        ('EXPENSE_BENEFITS', 'Gastos - Beneficios Sociales / Décimos'),
        ('EXPENSE_SOCIAL_SECURITY', 'Gastos - Aporte Patronal IESS'),
        ('LIABILITY_SALARIES_PAYABLE', 'Pasivo - Sueldos por Pagar'),
        ('LIABILITY_IESS_PAYABLE', 'Pasivo - IESS por Pagar'),
        ('LIABILITY_BENEFITS_PAYABLE', 'Pasivo - Beneficios Sociales por Pagar'),
    )

    key = models.CharField(max_length=50, choices=KEYS)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('institution', 'key')
        verbose_name = "Configuración Contable"
        verbose_name_plural = "Configuraciones Contables"

    def __str__(self):
        return f"{self.institution.name} : {self.get_key_display()} -> {self.account.code}"

class Bank(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    """
    Catálogo de Instituciones Financieras (Bancos, Cooperativas).
    """
    name = models.CharField(max_length=150, verbose_name="Nombre del Banco")
    code = models.CharField(max_length=50, blank=True, verbose_name="Código (Opcional/SRI)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('institution', 'name')
        verbose_name = "Banco"
        verbose_name_plural = "Bancos"

    def __str__(self):
        return self.name

class BankAccount(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    """
    Cuentas bancarias operativas de la Institución.
    """
    ACCOUNT_TYPES = (
        ('SAVINGS', 'Ahorros'),
        ('CHECKING', 'Corriente'),
        ('VIRTUAL', 'Billetera Virtual / Online'),
    )

    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name='accounts', verbose_name="Banco")
    
    account_number = models.CharField(max_length=50, verbose_name="Número de Cuenta")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='CHECKING', verbose_name="Tipo de Cuenta")
    
    # Enlace opcional al Plan de Cuentas Contable
    linked_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='bank_accounts', verbose_name="Cuenta Contable Asociada")
    
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Saldo Inicial")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('institution', 'bank', 'account_number')
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"

    def __str__(self):
        return f"{self.bank.name} - {self.get_account_type_display()} {self.account_number}"

class FixedAsset(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    """
    Activos Fijos de la Institución.
    """
    name = models.CharField(max_length=200, verbose_name="Nombre del Activo")
    code = models.CharField(max_length=50, blank=True, verbose_name="Código Interno / Etiqueta")
    
    purchase_date = models.DateField(verbose_name="Fecha de Compra")
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor de Adquisición")
    salvage_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Valor Residual (Salvamento)")
    useful_life_years = models.PositiveIntegerField(verbose_name="Vida Útil (Años)")
    
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Depreciación Acumulada")
    
    # Cuentas contables relacionadas
    account_asset = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='assets_as_asset', verbose_name="Cuenta de Activo")
    account_depreciation = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='assets_as_depreciation', verbose_name="Cuenta Depreciación Acumulada")
    account_expense = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='assets_as_expense', verbose_name="Cuenta Gasto por Depreciación")
    
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchase_date', 'name']
        verbose_name = "Activo Fijo"
        verbose_name_plural = "Activos Fijos"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def current_value(self):
        from decimal import Decimal
        return Decimal(str(self.purchase_price)) - Decimal(str(self.accumulated_depreciation))


class Depreciation(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    """
    Historial de Depreciaciones de un Activo Fijo.
    """
    asset = models.ForeignKey(FixedAsset, on_delete=models.CASCADE, related_name='depreciations')
    date = models.DateField(verbose_name="Fecha de Depreciación")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto Depreciado")
    
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name='depreciation_records')
    notes = models.CharField(max_length=255, blank=True, verbose_name="Notas / Periodo")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Registro de Depreciación"
        verbose_name_plural = "Registros de Depreciaciones"

    def __str__(self):
        return f"Dep. {self.asset.name} - {self.date} - ${self.amount}"
