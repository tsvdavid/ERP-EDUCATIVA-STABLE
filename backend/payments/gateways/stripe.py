import stripe
import json
from django.conf import settings
from rest_framework.exceptions import ValidationError
from payments.gateways.base import BasePaymentGateway
from payments.models import Transaction, PaymentLog, PaymentGatewayConfig

class StripeGateway(BasePaymentGateway):
    def __init__(self, institution=None):
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_placeholder')
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_placeholder')
        
        if institution:
            config = PaymentGatewayConfig.objects.filter(institution=institution, gateway_name='stripe', is_active=True).first()
            if config:
                stripe.api_key = config.credentials.get('secret_key', stripe.api_key)
                self.webhook_secret = config.credentials.get('webhook_secret', self.webhook_secret)

    def create_payment_intent(self, transaction):
        """
        Solicita a Stripe un intento de pago atado a la transacción local.
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(transaction.amount * 100), # Stripe usa centavos
                currency=transaction.currency.lower(),
                metadata={'transaction_id': transaction.id, 'reference_id': transaction.reference_id},
            )
            
            # Guardamos el ID del proveedor para seguimiento
            transaction.gateway_transaction_id = intent.id
            transaction.save(update_fields=['gateway_transaction_id'])
            
            return {
                'client_secret': intent.client_secret,
                'publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', 'pk_test_placeholder')
            }
        except stripe.error.StripeError as e:
            raise ValidationError(detail=str(e))

    def process_payment(self, payment_data):
        # Todo: Para Stripe comúnmente el front lo procesa con ConfirmCardPayment y JS
        pass

    def verify_status(self, gateway_transaction_id):
        try:
            intent = stripe.PaymentIntent.retrieve(gateway_transaction_id)
            return intent.status
        except stripe.error.StripeError as e:
            raise ValidationError(detail=str(e))

    def refund_payment(self, transaction_id, amount):
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            refund = stripe.Refund.create(
                payment_intent=transaction.gateway_transaction_id,
                amount=int(amount * 100)
            )
            transaction.status = Transaction.Status.REFUNDED
            transaction.save()
            return True
        except Exception as e:
            return False

    def handle_webhook(self, request_payload):
        """
        Parses the JSON coming from Stripe, logs it, and updates DB.
        """
        event = request_payload # Aqui se debería validar la firma con sig_header
        
        event_type = event.get('type')
        data_object = event.get('data', {}).get('object', {})
        
        intent_id = data_object.get('id')
        transaction = Transaction.objects.filter(gateway_transaction_id=intent_id).first()

        # Auditoria cruda de eventos
        PaymentLog.objects.create(
            transaction=transaction,
            gateway_name='stripe',
            event_type=event_type,
            payload=event
        )

        if not transaction:
            return {'status': 'ignored', 'reason': 'Transaction not found for intent_id'}

        if event_type == 'payment_intent.succeeded':
            transaction.status = Transaction.Status.PAID
            transaction.save()
            # AQUI: Llamar a los modulos internos para confirmar facturas.
        elif event_type == 'payment_intent.payment_failed':
            transaction.status = Transaction.Status.FAILED
            transaction.save()
            
        return {'status': 'success'}
