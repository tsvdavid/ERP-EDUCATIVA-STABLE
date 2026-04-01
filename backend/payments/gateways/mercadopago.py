import mercadopago
from django.conf import settings
from rest_framework.exceptions import ValidationError
from payments.gateways.base import BasePaymentGateway
from payments.models import Transaction, PaymentLog, PaymentGatewayConfig

class MercadoPagoGateway(BasePaymentGateway):
    """
    Integración con MercadoPago (Checkout SDK).
    """
    def __init__(self, institution=None):
        self.access_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', 'placeholder_access_token')
        
        if institution:
            config = PaymentGatewayConfig.objects.filter(institution=institution, gateway_name='mercadopago', is_active=True).first()
            if config and config.credentials.get('access_token'):
                self.access_token = config.credentials.get('access_token')
                
        self.sdk = mercadopago.SDK(self.access_token)

    def create_payment_intent(self, transaction):
        """
        Crea una Preferencia (Preference) en MercadoPago.
        Retorna la URL de init_point (Checkout Pro de MP) a donde se debe enviar al usuario.
        """
        try:
            # Bypass para demostración/desarrollo sin keys reales
            if self.access_token == 'placeholder_access_token':
                transaction.gateway_transaction_id = f"demo_mp_{transaction.id}"
                transaction.save(update_fields=['gateway_transaction_id'])
                return {
                    'preference_id': transaction.gateway_transaction_id,
                    'init_point': f"https://sandbox.mercadopago.com/checkout/pay?pref_id={transaction.gateway_transaction_id}",
                    'sandbox_init_point': f"https://sandbox.mercadopago.com/checkout/pay?pref_id={transaction.gateway_transaction_id}",
                }

            preference_data = {
                "items": [
                    {
                        "id": str(transaction.reference_id),
                        "title": transaction.description or f"Order {transaction.reference_id}",
                        "quantity": 1,
                        "currency_id": transaction.currency.upper(),
                        "unit_price": float(transaction.amount)
                    }
                ],
                "external_reference": str(transaction.id), # Nuestra transacción ID interna
                "back_urls": {
                    "success": getattr(settings, 'MERCADOPAGO_RETURN_URL_SUCCESS', 'http://localhost:3000/payments/success'),
                    "failure": getattr(settings, 'MERCADOPAGO_RETURN_URL_FAILURE', 'http://localhost:3000/payments/cancel'),
                    "pending": getattr(settings, 'MERCADOPAGO_RETURN_URL_PENDING', 'http://localhost:3000/payments/pending')
                },
                "auto_return": "approved",
                # Opcional: Para webhooks
            }
            
            webhook_url = getattr(settings, 'MERCADOPAGO_WEBHOOK_URL', 'https://tu-dominio.com/api/payments/webhook/mercadopago/')
            institution_id = getattr(getattr(transaction.user, 'institution', None), 'id', None)
            if institution_id:
                separator = '&' if '?' in webhook_url else '?'
                webhook_url += f"{separator}institution_id={institution_id}"
                
            preference_data["notification_url"] = webhook_url

            preference_response = self.sdk.preference().create(preference_data)
            preference = preference_response["response"]
            
            # Guardamos el ID de preferencia
            transaction.gateway_transaction_id = preference['id']
            transaction.save(update_fields=['gateway_transaction_id'])

            return {
                'preference_id': preference['id'],
                'init_point': preference['init_point'], # Modo producción
                'sandbox_init_point': preference['sandbox_init_point'], # Modo test
            }

        except Exception as e:
            raise ValidationError(detail=str(e))

    def process_payment(self, payment_data):
        # Checkout API requiere que el frontal use Brick o vuelva desde el init_point
        pass

    def verify_status(self, gateway_transaction_id):
        # MP se basa más en Webhooks, pero se podría buscar el pago por external_reference
        pass

    def refund_payment(self, transaction_id, amount):
        pass

    def handle_webhook(self, request_payload):
        """
        Maneja Notificaciones IPN o Webhooks de MercadoPago.
        Generalmente MP solo avisa "Oye, revisa el recurso ID X" y nosotros vamos a buscarlo.
        """
        # Nota: MercadoPago manda { "type": "payment", "data": { "id": "123456" } } (Webhooks)
        # o { "topic": "payment", "id": "123456" } (IPN)
        topic = request_payload.get("type", request_payload.get("topic"))
        data_id = request_payload.get("data", {}).get("id", request_payload.get("id"))
        
        # Auditoria cruda
        PaymentLog.objects.create(
            gateway_name='mercadopago',
            event_type=f"webhook_{topic}",
            payload=request_payload
        )

        if str(topic) == "payment" and data_id:
            try:
                # 1. Consultar a MercadoPago por el estado real de este pago
                payment_info = self.sdk.payment().get(data_id)
                payment = payment_info["response"]
                
                status_mp = payment.get("status") # 'approved', 'rejected', 'in_process'...
                external_reference = payment.get("external_reference") # Este es nuestro transaction.id original!

                if not external_reference:
                    return {'status': 'ignored', 'reason': 'No external_reference found in payment'}
                
                transaction = Transaction.objects.filter(id=external_reference).first()
                if not transaction:
                    return {'status': 'ignored', 'reason': 'Transaction not found for external_reference'}
                
                # Actualizar log con la trx
                PaymentLog.objects.create(
                    transaction=transaction,
                    gateway_name='mercadopago',
                    event_type=f"status_{status_mp}",
                    payload=payment
                )

                if status_mp == 'approved':
                    if transaction.status != Transaction.Status.PAID:
                        transaction.status = Transaction.Status.PAID
                        transaction.save()
                        # AQUI: Cerramos la factura (usando Senales o Callback)
                        
                elif status_mp in ['rejected', 'cancelled', 'refunded']:
                    transaction.status = Transaction.Status.FAILED
                    transaction.save()

                return {'status': 'success'}
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error revisando pago MercadoPago: {str(e)}")
                return {'status': 'error'}

        return {'status': 'ignored', 'reason': 'Topic not handled'}
