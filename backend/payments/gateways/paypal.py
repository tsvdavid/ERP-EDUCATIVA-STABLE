import urllib.parse
import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError
from payments.gateways.base import BasePaymentGateway
from payments.models import Transaction, PaymentLog, PaymentGatewayConfig

class PayPalGateway(BasePaymentGateway):
    """
    Integración con PayPal (REST API v2).
    """
    def __init__(self, institution=None):
        self.client_id = getattr(settings, 'PAYPAL_CLIENT_ID', 'placeholder_client_id')
        self.client_secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', 'placeholder_secret')
        self.mode = getattr(settings, 'PAYPAL_MODE', 'sandbox') # 'sandbox' | 'live'
        
        if institution:
            config = PaymentGatewayConfig.objects.filter(institution=institution, gateway_name='paypal', is_active=True).first()
            if config:
                self.client_id = config.credentials.get('client_id', self.client_id)
                self.client_secret = config.credentials.get('client_secret', self.client_secret)
                self.mode = 'sandbox' if config.is_test_mode else 'live'
        
        if self.mode == 'live':
            self.base_url = "https://api-m.paypal.com"
        else:
            self.base_url = "https://api-m.sandbox.paypal.com"

    def _get_access_token(self):
        """Obtiene un Bearer token de PayPal para hacer llamadas a la API."""
        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {
            "grant_type": "client_credentials"
        }
        response = requests.post(url, headers=headers, data=data, auth=(self.client_id, self.client_secret))
        
        if response.status_code != 200:
            raise ValidationError(f"Error autenticando con PayPal: {response.text}")
            
        return response.json().get('access_token')

    def create_payment_intent(self, transaction):
        """
        Crea una Orden (Order) en PayPal para cobrar el monto exacto.
        """
        try:
            # Bypass para demostración/desarrollo sin keys reales
            if self.client_id == 'placeholder_client_id':
                transaction.gateway_transaction_id = f"demo_paypal_{transaction.id}"
                transaction.save(update_fields=['gateway_transaction_id'])
                return {
                    'order_id': transaction.gateway_transaction_id,
                    'approve_url': f"https://www.sandbox.paypal.com/checkoutnow?token={transaction.gateway_transaction_id}",
                }

            token = self._get_access_token()
            url = f"{self.base_url}/v2/checkout/orders"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            
            # Construir el payload V2
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": str(transaction.id), # Nuestra referencia interna fuerte
                        "amount": {
                            "currency_code": transaction.currency.upper(),
                            "value": str(transaction.amount) # Formato string '10.50'
                        },
                        "description": transaction.description or f"Order {transaction.reference_id}"
                    }
                ],
                "application_context": {
                    "return_url": getattr(settings, 'PAYPAL_RETURN_URL', 'http://localhost:3000/payments/success'),
                    "cancel_url": getattr(settings, 'PAYPAL_CANCEL_URL', 'http://localhost:3000/payments/cancel'),
                    "user_action": "PAY_NOW"
                }
            }

            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            if response.status_code not in [200, 201]:
                raise ValidationError(f"Error creando Orden en PayPal: {response_data}")

            # Identificador Maestro
            order_id = response_data.get('id')
            transaction.gateway_transaction_id = order_id
            transaction.save(update_fields=['gateway_transaction_id'])
            
            # Buscar el link de aprobación ('approve')
            approve_link = next((link['href'] for link in response_data.get('links', []) if link['rel'] == 'approve'), None)

            return {
                'order_id': order_id,
                'approve_url': approve_link, # Frontend redirige aquí
            }

        except Exception as e:
            raise ValidationError(detail=str(e))

    def process_payment(self, payment_data):
        # Generalmente, tras redirigir al approve_url, PayPal redirige al app context
        # Podríamos hacer el Capture on Return aquí.
        pass

    def verify_status(self, gateway_transaction_id):
        """Consulta directamente la orden para ver si fue pagada."""
        try:
            token = self._get_access_token()
            url = f"{self.base_url}/v2/checkout/orders/{gateway_transaction_id}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get('status')
            return "UNKNOWN"
            
        except Exception as e:
            raise ValidationError(detail=str(e))

    def refund_payment(self, transaction_id, amount):
        pass

    def handle_webhook(self, request_payload):
        """
        Recibe las notificaciones de eventos (ej. PAYMENT.CAPTURE.COMPLETED).
        """
        event = request_payload
        
        event_type = event.get('event_type')
        resource = event.get('resource', {})
        
        # En PayPal, el resource.id del evento capture *no* es el Order ID, 
        # sino que está en supplementary_data o parent_payment o invoice_id... 
        # Depende fuertemente del mapping, pero asumimos custom_id o reference_id
        
        # Auditoria
        try:
            # Buscar transacción base
            # Lo más fiable en event capture completion es extraer el reference_id (nuestro trasaction_id) o purchase_units
            custom_internal_id = None
            if 'custom_id' in resource:
                 custom_internal_id = resource['custom_id']
            elif 'supplementary_data' in resource and 'related_ids' in resource['supplementary_data']:
                 custom_internal_id = resource['supplementary_data']['related_ids'].get('order_id')
            
            # Alternativa: Buscar por related order ID si se puede
            # En PayPal V2, un Webhook PAYMENT.CAPTURE.COMPLETED tiene un campo 'supplementary_data'.'related_ids'.'order_id'
            order_id = resource.get('supplementary_data', {}).get('related_ids', {}).get('order_id')
            if not order_id and 'id' in resource and event_type.startswith('CHECKOUT.ORDER'):
                order_id = resource.get('id')

            transaction = None
            if order_id:
                transaction = Transaction.objects.filter(gateway_transaction_id=order_id).first()

            # Guardar auditoria sea que se encuentre o no
            if transaction:
                PaymentLog.objects.create(transaction=transaction, gateway_name='paypal', event_type=event_type, payload=event)
            else:
                 # No se pudo resolver
                 PaymentLog.objects.create(gateway_name='paypal', event_type=event_type, payload=event)

            if not transaction:
                return {'status': 'ignored', 'reason': 'Transaction not found for order_id'}

            if event_type in ['PAYMENT.CAPTURE.COMPLETED', 'CHECKOUT.ORDER.APPROVED']:
                if transaction.status != Transaction.Status.PAID:
                    transaction.status = Transaction.Status.PAID
                    transaction.save()
                    # AQUI: Llamar lógica de cerrar factura
            
            elif event_type in ['PAYMENT.CAPTURE.DENIED', 'CHECKOUT.ORDER.VOIDED']:
                transaction.status = Transaction.Status.FAILED
                transaction.save()

            return {'status': 'success'}
            
        except Exception as e:
            # Si explota capturarlo para no alertar a PayPal con un 500
            import logging
            logging.getLogger(__name__).error(f"Error procesando Webhook PayPal: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    # Todo: Agrega función para "Capture" Order porque Approval no transfiere los fondos automáticamente
