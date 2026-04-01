from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pendiente')
        VERIFYING = 'VERIFYING', _('En Verificación')
        PAID = 'PAID', _('Pagado')
        CANCELED = 'CANCELED', _('Cancelado')
        FAILED = 'FAILED', _('Fallido')
        REFUNDED = 'REFUNDED', _('Reembolsado')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto a cobrar")
    currency = models.CharField(max_length=3, default='USD', help_text="Moneda (ej USD)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Comprobantes de transferencia u otros métodos manuales
    voucher_file = models.FileField(upload_to='vouchers/%Y/%m/', null=True, blank=True, help_text="Archivo de comprobante de depósito")
    
    # Referencias de integraciones
    gateway_name = models.CharField(max_length=50, blank=True, help_text="Nombre proveedor ej. stripe, payphone")
    gateway_transaction_id = models.CharField(max_length=255, blank=True, help_text="Token o ID remoto del proveedor")
    
    # Internal relations (Facturas, Pedidos)
    reference_id = models.CharField(max_length=100, blank=True, help_text="ID de Factura o Pedido que originó el pago")
    description = models.CharField(max_length=255, blank=True, help_text="Concepto ej. Pago de Mensualidad Septiembre")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Transacción')
        verbose_name_plural = _('Transacciones')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.amount} {self.currency} [{self.status}]"


class PaymentLog(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    gateway_name = models.CharField(max_length=50, blank=True)
    event_type = models.CharField(max_length=100, help_text="Tipo de evento: webhook, webhook_failed, charge_created")
    payload = models.JSONField(help_text="Carga cruda JSON enviada o recibida")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Registro de Pago (Log)')
        verbose_name_plural = _('Registros de Pagos')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.gateway_name} - {self.event_type} - {self.created_at}"

class PaymentGatewayConfig(models.Model):
    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, related_name='payment_gateways')
    gateway_name = models.CharField(max_length=50, help_text="Ej: stripe, paypal, mercadopago, payphone")
    
    is_active = models.BooleanField(default=False, help_text="¿Está habilitada esta pasarela para la institución?")
    is_test_mode = models.BooleanField(default=True, help_text="Si es True, usará credenciales/entorno Sandbox")
    
    # Store credentials as JSON. In a real highly-secure prod env, this should use django-fernet-fields or similar.
    credentials = models.JSONField(default=dict, blank=True, help_text="Llaves API en formato JSON. Ej: {'client_id': '...', 'secret': '...'}")

    class Meta:
        verbose_name = _('Configuración de Pasarela')
        verbose_name_plural = _('Configuraciones de Pasarelas')
        constraints = [
            models.UniqueConstraint(fields=['institution', 'gateway_name'], name='unique_gateway_per_institution')
        ]

    def __str__(self):
        return f"{self.gateway_name} ({'Activa' if self.is_active else 'Inactiva'}) - {self.institution.name}"
