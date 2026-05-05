from django.db import models
from django.db.models import Q
from users.models import User, Institution
from core.models import TenantModel

from decimal import Decimal

class Customer(TenantModel):
    class CustomerType(models.TextChoices):
        STUDENT = 'STUDENT', 'Académico (Estudiante)'
        INDIVIDUAL = 'INDIVIDUAL', 'Individual'
        COMPANY = 'COMPANY', 'Empresa / RUC'
        WALKIN = 'WALKIN', 'Consumidor Final'

    customer_type = models.CharField(max_length=20, choices=CustomerType.choices, default=CustomerType.STUDENT)
    student = models.OneToOneField(
        'users.User', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='customer_profile',
        limit_choices_to={'role': 'STUDENT'}
    )
    identification = models.CharField(max_length=20)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True, default='')
    business_name = models.CharField(max_length=255, blank=True, default='')
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.identification} - {self.first_name} {self.last_name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'identification'], name='unique_customer_per_institution')
        ]


class PaymentMethod(TenantModel):
    name = models.CharField(max_length=50) # Efectivo, Transferencia, etc.
    code = models.CharField(max_length=20) # SRI code if needed or internal
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'code'], name='unique_code_per_institution')
        ]

    def __str__(self):
        return self.name

class PaymentConcept(TenantModel):
    """
    Defines what can be paid: 'Matricula 2024', 'Pension Marzo', etc.
    """
    IVA_CHOICES = (
        (Decimal('0.00'), '0%'),
        (Decimal('0.15'), '15%'),
    )

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    iva_rate = models.DecimalField(max_digits=4, decimal_places=2, choices=IVA_CHOICES, default=Decimal('0.00'))
    is_recurring = models.BooleanField(default=False) # If true, generated monthly?
    due_day = models.PositiveIntegerField(null=True, blank=True) # e.g., 5th of each month
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

class StudentAccount(TenantModel):
    """
    Tracks the balance of a student.
    Positive Balance = Student owes money.
    Negative Balance = Student has credit (overpaid).
    """
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account', limit_choices_to={'role': 'STUDENT'})
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Account: {self.student.username} - Balance: ${self.balance}"

class Invoice(TenantModel):
    """
    Represents a formal financial document (Factura or Recibo).
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('ISSUED', 'Emitida'),
        ('CANCELLED', 'Anulada'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices', null=True, blank=True)
    student = models.ForeignKey(User, on_delete=models.PROTECT, related_name='invoices', null=True, blank=True)
    
    # Header Info
    number = models.CharField(max_length=20) # Sequence number (001-001-000000001)
    issue_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    # SRI - Facturación Electrónica
    access_key = models.CharField(max_length=49, unique=True, null=True, blank=True, verbose_name="Clave de Acceso")
    sri_version = models.CharField(max_length=10, default='1.0.0', verbose_name="Versión XML")
    xml_content = models.TextField(blank=True, null=True, verbose_name="XML Firmado")
    sri_response = models.JSONField(blank=True, null=True, verbose_name="Respuesta SRI")
    sri_authorization_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Autorización")
    sri_status = models.CharField(
        max_length=20, 
        choices=[
            ('DRAFT', 'Borrador'),
            ('SIGNED', 'Firmado'),
            ('PENDING_SRI', 'Pendiente Reintento (SRI 500)'),
            ('RECEIVED', 'Recibido por SRI'),
            ('AUTHORIZED', 'Autorizado'),
            ('REJECTED', 'Rechazado')
        ],
        default='DRAFT',
        verbose_name="Estado SRI"
    )
    sri_attempts = models.PositiveIntegerField(default=0, verbose_name="Intentos SRI")
    
    # Billing Info (Data for SRI)
    client_name = models.CharField(max_length=200)
    client_ruc = models.CharField(max_length=13) # RUC or Cedula
    client_address = models.TextField(blank=True)
    client_email = models.EmailField(blank=True)

    # Totals
    subtotal_0 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    subtotal_15 = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    iva_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    transaction_reference = models.CharField(max_length=100, blank=True) # Check #, Transfer ID

    # Email Tracking
    EMAIL_STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviado'),
        ('FAILED', 'Fallido'),
        ('RETRYING', 'Reintentando'),
    ]
    email_status = models.CharField(max_length=20, choices=EMAIL_STATUS_CHOICES, default='PENDING', verbose_name="Estado Envío Email")
    last_email_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Último Envío Email")
    email_attempts_count = models.PositiveIntegerField(default=0, verbose_name="Intentos de Envío")
    last_email_log = models.ForeignKey('notifications.EmailLog', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_last_log')

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='issued_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice #{self.number} - {self.client_name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'number'], name='unique_invoice_number_per_institution'),
            models.CheckConstraint(
                condition=Q(student__isnull=False) | ~Q(client_name=''),
                name='invoice_student_or_client_name'
            )
        ]

class Charge(TenantModel):
    """
    Represents a debt/receivable (Account Receivable).
    e.g. "Pension Noviembre" for Student X.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='charges', null=True, blank=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='charges', limit_choices_to={'role': 'STUDENT'}, null=True, blank=True)
    concept = models.ForeignKey(PaymentConcept, on_delete=models.PROTECT)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Snapshot of price
    
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    
    # Optional: If partial payments were allowed, we'd need 'balance'. For now, binary paid/not.
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.student.username if self.student else (f"{self.customer.first_name} {self.customer.last_name}" if self.customer else "Individual")
        return f"Charge: {name} - {self.concept.name} - ${self.amount}"

class InvoiceDetail(TenantModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='details')
    
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    concept = models.ForeignKey(PaymentConcept, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Link to the Charge being paid (optional, if it was a debt payment)
    charge = models.OneToOneField(Charge, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_detail')

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

class Payment(TenantModel):
    """
    Log of a payment received, linked to an invoice.
    Ideally 1 Invoice = 1 Payment Transaction in this simple model.
    """
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='payment')
    
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=True) # Cashier verified funds

    def __str__(self):
        return f"Payment for {self.invoice.number} - ${self.amount_paid}"

class CreditNote(TenantModel):
    STATUS_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('ISSUED', 'Emitida'),
        ('CANCELLED', 'Anulada'),
    )
    
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='credit_notes')
    number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    reason = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nota de Crédito #{self.number} - Factura {self.invoice.number}"

class DebitNote(TenantModel):
    STATUS_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('ISSUED', 'Emitida'),
        ('CANCELLED', 'Anulada'),
    )
    
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, null=False, related_name="%(class)s_related")
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='debit_notes')
    number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    reason = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nota de Débito #{self.number} - Factura {self.invoice.number}"

class InvoiceSequence(TenantModel):
    """
    Tracks the next available sequence number for invoices per establishment and emission point.
    Prevents race conditions using select_for_update().
    """
    establishment = models.CharField(max_length=3, default='001')
    emission_point = models.CharField(max_length=3, default='001')
    next_number = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['institution', 'establishment', 'emission_point'], 
                name='unique_sequence_per_point'
            )
        ]
    
    def __str__(self):
        return f"{self.institution.name} - {self.establishment}-{self.emission_point}: {self.next_number}"
