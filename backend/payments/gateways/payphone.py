import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError
from payments.gateways.base import BasePaymentGateway
from payments.models import Transaction, PaymentLog, PaymentGatewayConfig

class PayPhoneGateway(BasePaymentGateway):
    """
    Integración con PayPhone (Ecuador).
    Usando API REST Button/Prepare y Confirm.
    """
    def __init__(self, institution=None):
        self.token = getattr(settings, 'PAYPHONE_AUTHORIZATION_TOKEN', 'placeholder_token')
        self.base_url = getattr(settings, 'PAYPHONE_BASE_URL', 'https://pay.payphonetodoesposible.com/api')
        
        if institution:
            config = PaymentGatewayConfig.objects.filter(institution=institution, gateway_name='payphone', is_active=True).first()
            if config:
                self.token = config.credentials.get('token', self.token)
                self.base_url = "https://pay.payphonetodoesposible.com/api" if config.is_test_mode else "https://pay.payphonetodoesposible.com/api"

    def create_payment_intent(self, transaction):
        """
        Prepara el pago en PayPhone.
        """
        try:
            # Bypass para demostración/desarrollo sin keys reales
            if self.token == 'placeholder_token':
                client_txn_id = f"TX_{transaction.id}_DEMO"
                transaction.gateway_transaction_id = f"demo_payphone_{transaction.id}"
                transaction.description = f"{transaction.description} [CTX:{client_txn_id}]"
                transaction.save(update_fields=['gateway_transaction_id', 'description'])
                return {
                    'payment_id': transaction.gateway_transaction_id,
                    'client_transaction_id': client_txn_id,
                    'pay_url': f"https://payphone.app/sandbox/demo-checkout/{transaction.id}?amount={transaction.amount}"
                }

            url = f"{self.base_url}/button/Prepare"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Payphone pide un clientTransactionId único por pago
            client_txn_id = f"TX_{transaction.id}_{transaction.created_at.strftime('%Y%m%d%H%M%S')}"

            data = {
                "responseUrl": getattr(settings, 'PAYPHONE_RESPONSE_URL', 'http://localhost:3000/payments/payphone/return'),
                "cancelUrl": getattr(settings, 'PAYPHONE_CANCEL_URL', 'http://localhost:3000/payments/cancel'),
                "amount": int(transaction.amount * 100), # centavos
                "amountWithoutTax": int(transaction.amount * 100),
                "amountWithTax": 0,
                "tax": 0,
                "clientTransactionId": client_txn_id,
                "currency": transaction.currency.upper(),
                "reference": str(transaction.reference_id or transaction.id)
            }
            
            response = requests.post(url, json=data, headers=headers)
            response_data = response.json()
            
            if response.status_code != 200:
                raise ValidationError(f"Error preparando pago PayPhone: {response.text}")

            payment_id = response_data.get('paymentId')
            transaction.gateway_transaction_id = str(payment_id)
            # Guardamos también el clientTransactionId dentro del description para futuras referencias cruzadas
            transaction.description = f"{transaction.description} [CTX:{client_txn_id}]"
            transaction.save(update_fields=['gateway_transaction_id', 'description'])
            
            return {
                'payment_id': payment_id,
                'client_transaction_id': client_txn_id,
                'pay_url': response_data.get('payWithBrowser') # Frontend redirige a esta URL
            }

        except Exception as e:
            raise ValidationError(detail=str(e))

    def process_payment(self, payment_data):
        pass

    def verify_status(self, gateway_transaction_id):
        """No hay polling directo común en la versión base sin un clientTxId, 
        pero el webhook es la preferencia."""
        pass

    def refund_payment(self, transaction_id, amount):
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            url = f"{self.base_url}/button/Reverse"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            # Se necesita el id exacto devuelto por PayPhone en la confirmacion, asumiendo guardado en gateway_trx_id
            data = { "id": int(transaction.gateway_transaction_id) }
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                 transaction.status = Transaction.Status.REFUNDED
                 transaction.save()
                 return True
            return False
        except Exception:
            return False

    def handle_webhook(self, request_payload):
        """
        PayPhone suele notificar a través de comprobación de status si se configura, 
        o la App redirige de vuelta a un Endpoint que nosotros tomariamos como Webhook/Confirmación.
        Este Endpoint asume el flujo de validiar usando el `id` y `clientTxId`.
        """
        try:
            # PayPhone tipicamente puede llamar a un webhook si la transaccion cambia a approved.
            payment_id = request_payload.get('id')
            client_tx_id = request_payload.get('clientTransactionId')
            
            if not payment_id:
                 return {'status': 'ignored', 'reason': 'No payment id'}
                 
            transaction = Transaction.objects.filter(gateway_transaction_id=str(payment_id)).first()
            if transaction:
                 PaymentLog.objects.create(
                     transaction=transaction,
                     gateway_name='payphone',
                     event_type="status_notification",
                     payload=request_payload
                 )
                 
                 # Verificar estado real de Payphone
                 status_pp = request_payload.get('transactionStatus') 
                 if status_pp == 'Approved':
                      if transaction.status != Transaction.Status.PAID:
                           transaction.status = Transaction.Status.PAID
                           transaction.save()
                 elif status_pp in ['Canceled', 'Declined']:
                      transaction.status = Transaction.Status.FAILED
                      transaction.save()
                 return {'status': 'success'}
                 
            return {'status': 'ignored', 'reason': 'Transaction not found'}
        except Exception as e:
             return {'status': 'error', 'message': str(e)}
