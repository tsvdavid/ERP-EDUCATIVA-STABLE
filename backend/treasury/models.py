from django.db import models
from users.models import User, Institution

from decimal import Decimal

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50) # Efectivo, Transferencia, etc.
    code = models.CharField(max_length=20) # SRI code if needed or internal
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='payment_methods')
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'code'], name='unique_code_per_institution')
        ]

    def __str__(self):
        return self.name

class PaymentConcept(models.Model):
    """
    Defines what can be paid: 'Matricula 2024', 'Pension Marzo', etc.
    """
    IVA_CHOICES = (
        (Decimal('0.00'), '0%'),
        (Decimal('0.15'), '15%'),
    )

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='concepts')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    iva_rate = models.DecimalField(max_digits=4, decimal_places=2, choices=IVA_CHOICES, default=Decimal('0.00'))
    is_recurring = models.BooleanField(default=False) # If true, generated monthly?
    due_day = models.PositiveIntegerField(null=True, blank=True) # e.g., 5th of each month
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

class StudentAccount(models.Model):
    """
    Tracks the balance of a student.
    Positive Balance = Student owes money.
    Negative Balance = Student has credit (overpaid).
    """
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account', limit_choices_to={'role': 'STUDENT'})
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Account: {self.student.username} - Balance: ${self.balance}"

class Invoice(models.Model):
    """
    Represents a formal financial document (Factura or Recibo).
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Borrador'),
        ('ISSUED', 'Emitida'),
        ('CANCELLED', 'Anulada'),
    )

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.PROTECT, related_name='invoices')
    
    # Header Info
    number = models.CharField(max_length=20, unique=True) # Sequence number
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
            ('PENDING', 'Pendiente'),
            ('SENT', 'Enviado'),
            ('AUTHORIZED', 'Autorizado'),
            ('REJECTED', 'Rechazado')
        ],
        default='PENDING',
        verbose_name="Estado SRI"
    )
    
    # Billing Info (Data for SRI)
    client_name = models.CharField(max_length=200)
    client_ruc = models.CharField(max_length=13) # RUC or Cedula
    client_address = models.TextField(blank=True)
    client_email = models.EmailField(blank=True)

    # Totals
    subtotal_0 = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal_15 = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    iva_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    transaction_reference = models.CharField(max_length=100, blank=True) # Check #, Transfer ID

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='issued_invoices')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.number} - {self.client_name}"

class Charge(models.Model):
    """
    Represents a debt/receivable (Account Receivable).
    e.g. "Pension Noviembre" for Student X.
    """
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='charges', limit_choices_to={'role': 'STUDENT'})
    concept = models.ForeignKey(PaymentConcept, on_delete=models.PROTECT)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Snapshot of price
    
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    
    # Optional: If partial payments were allowed, we'd need 'balance'. For now, binary paid/not.
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Charge: {self.student.username} - {self.concept.name} - ${self.amount}"

class InvoiceDetail(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='details')
    concept = models.ForeignKey(PaymentConcept, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Link to the Charge being paid (optional, if it was a debt payment)
    charge = models.OneToOneField(Charge, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_detail')

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

class Payment(models.Model):
    """
    Log of a payment received, linked to an invoice.
    Ideally 1 Invoice = 1 Payment Transaction in this simple model.
    """
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='payment')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=True) # Cashier verified funds

    def __str__(self):
        return f"Payment for {self.invoice.number} - ${self.amount_paid}"
