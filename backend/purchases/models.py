from django.db import models
from users.models import Institution, User
from accounting.models import Account
from core.models import TenantModel
from decimal import Decimal

class Supplier(TenantModel):
    """
    Proveedor (Vendor/Supplier).
    """
    TAX_ID_TYPE_CHOICES = (
        ('RUC', 'RUC'),
        ('CEDULA', 'Cédula'),
        ('PASAPORTE', 'Pasaporte'),
    )

    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    tax_id = models.CharField(max_length=20, verbose_name="Identificación (RUC/CI)")
    tax_id_type = models.CharField(max_length=20, choices=TAX_ID_TYPE_CHOICES, default='RUC')
    
    legal_name = models.CharField(max_length=255, verbose_name="Razón Social")
    trade_name = models.CharField(max_length=255, blank=True, verbose_name="Nombre Comercial")
    
    address = models.TextField(blank=True, verbose_name="Dirección")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Teléfono")
    
    is_special_taxpayer = models.BooleanField(default=False, verbose_name="Es Contribuyente Especial")
    establishment_code = models.CharField(max_length=3, default='001', blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('institution', 'tax_id')
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return f"{self.tax_id} - {self.legal_name}"

class PurchaseInvoice(TenantModel):
    """
    Factura de Compra recibida de un proveedor.
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('VALIDATED', 'Validada/Contabilizada'),
        ('CANCELLED', 'Anulada'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('01', 'Sin utilización del sistema financiero'),
        ('19', 'Tarjeta de crédito'),
        ('20', 'Otros con utilización del sistema financiero'),
        # Add more simplified choices as needed
    )

    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='invoices')
    
    # Document Info
    document_number = models.CharField(max_length=17, verbose_name="Número Comprobante") # 001-001-000000001
    authorization_code = models.CharField(max_length=49, blank=True, verbose_name="Clave Acceso / Autorización")
    
    issue_date = models.DateField(verbose_name="Fecha Emisión")
    registration_date = models.DateField(auto_now_add=True, verbose_name="Fecha Registro")
    
    sustento_tributario = models.CharField(max_length=2, default='01', verbose_name="Cod. Sustento")
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='20')

    # Totals
    subtotal_0 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_no_obj = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Accounting Link
    journal_entry_id = models.IntegerField(null=True, blank=True) # Soft link to accounting entry

    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.supplier.legal_name} - {self.document_number}"
        
    def save(self, *args, **kwargs):
        # Calc Total auto? Or trust user input? For purchases, usually we match the physical doc.
        # But we can enforce simple integrity
        self.total = self.subtotal_0 + self.subtotal_15 + self.subtotal_no_obj + self.iva
        super().save(*args, **kwargs)

class PurchaseItem(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    
    # Expense Account
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Cuenta de Gasto")
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, choices=[(Decimal('0'), '0%'), (Decimal('15'), '15%')], default=Decimal('0'))

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Withholding(TenantModel):
    """
    Comprobante de Retención emitido al proveedor.
    """
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    purchase_invoice = models.OneToOneField(PurchaseInvoice, on_delete=models.CASCADE, related_name='withholding')
    
    document_number = models.CharField(max_length=17, verbose_name="Número Retención") 
    issue_date = models.DateField()
    access_key = models.CharField(max_length=49, unique=True, null=True, blank=True)
    
    # Values
    ret_renta_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    ret_renta_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    ret_renta_code = models.CharField(max_length=10, blank=True, verbose_name="Cod. Retención Renta")
    
    ret_iva_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    ret_iva_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    sri_status = models.CharField(max_length=20, default='PENDING')

    def __str__(self):
        return f"Ret {self.document_number} - {self.purchase_invoice.supplier.legal_name}"

class PurchaseCreditNote(TenantModel):
    """
    Nota de Crédito recibida de un proveedor (Devolución / Descuento posterior).
    """
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.PROTECT, related_name='credit_notes', verbose_name="Factura Modificada")
    
    document_number = models.CharField(max_length=17, verbose_name="Número Nota Crédito", unique=True)
    authorization_code = models.CharField(max_length=49, blank=True, verbose_name="Clave Acceso NC")
    issue_date = models.DateField(verbose_name="Fecha Emisión")
    
    reason = models.CharField(max_length=255, verbose_name="Motivo de Modificación")
    
    subtotal_0 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_no_obj = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NC {self.document_number} - {self.invoice.supplier.legal_name}"
        
    def save(self, *args, **kwargs):
        self.total = self.subtotal_0 + self.subtotal_15 + self.subtotal_no_obj + self.iva
        super().save(*args, **kwargs)

class PurchaseDebitNote(TenantModel):
    """
    Nota de Débito recibida de un proveedor (Aumento de valor / Intereses).
    """
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.PROTECT, related_name='debit_notes', verbose_name="Factura Modificada")
    
    document_number = models.CharField(max_length=17, verbose_name="Número Nota Débito", unique=True)
    authorization_code = models.CharField(max_length=49, blank=True, verbose_name="Clave Acceso ND")
    issue_date = models.DateField(verbose_name="Fecha Emisión")
    
    reason = models.CharField(max_length=255, verbose_name="Motivo de Modificación")
    
    subtotal_0 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_no_obj = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ND {self.document_number} - {self.invoice.supplier.legal_name}"
        
    def save(self, *args, **kwargs):
        self.total = self.subtotal_0 + self.subtotal_15 + self.subtotal_no_obj + self.iva
        super().save(*args, **kwargs)

class PurchaseLiquidation(TenantModel):
    """
    Liquidación de Compra emitida por la institución a un proveedor (generalmente sin RUC).
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('VALIDATED', 'Validada/Contabilizada'),
        ('CANCELLED', 'Anulada'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('01', 'Sin utilización del sistema financiero'),
        ('19', 'Tarjeta de crédito'),
        ('20', 'Otros con utilización del sistema financiero'),
    )

    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='liquidations')
    
    document_number = models.CharField(max_length=17, verbose_name="Número Comprobante") 
    authorization_code = models.CharField(max_length=49, blank=True, verbose_name="Clave Acceso / Autorización")
    
    issue_date = models.DateField(verbose_name="Fecha Emisión")
    registration_date = models.DateField(auto_now_add=True, verbose_name="Fecha Registro")
    
    sustento_tributario = models.CharField(max_length=2, default='01', verbose_name="Cod. Sustento")
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='20')

    subtotal_0 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_no_obj = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    journal_entry_id = models.IntegerField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.supplier.legal_name} - {self.document_number}"
        
    def save(self, *args, **kwargs):
        self.total = self.subtotal_0 + self.subtotal_15 + self.subtotal_no_obj + self.iva
        super().save(*args, **kwargs)

class PurchaseLiquidationItem(TenantModel):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    liquidation = models.ForeignKey(PurchaseLiquidation, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Cuenta de Gasto")
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, choices=[(Decimal('0'), '0%'), (Decimal('15'), '15%')], default=Decimal('0'))

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
