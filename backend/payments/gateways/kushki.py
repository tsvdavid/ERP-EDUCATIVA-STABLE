import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError
from payments.gateways.base import BasePaymentGateway
from payments.models import Transaction, PaymentLog

class KushkiGateway(BasePaymentGateway):
    """
    Integración con Kushki (Latam).
    """
    def __init__(self):
        self.merchant_id = getattr(settings, 'KUSHKI_MERCHANT_ID', 'placeholder_merchant')
        self.public_key = getattr(settings, 'KUSHKI_PUBLIC_KEY', 'placeholder_public')
        self.private_key = getattr(settings, 'KUSHKI_PRIVATE_KEY', 'placeholder_private')
        self.is_test = getattr(settings, 'KUSHKI_TEST_MODE', True)
        
        if self.is_test:
            self.base_url = "https://api-uat.kushkipagos.com"
        else:
            self.base_url = "https://api.kushkipagos.com"

    def create_payment_intent(self, transaction):
        """
        Retorna la clave pública y datos para que el frontend levante Cajita de Kushki
        y obtenga el token. Kushki funciona primariamente entregando un token por el Frontend 
        y el Backend lo captura (process_payment).
        """
        return {
            'public_key': self.public_key,
            'merchant_id': self.merchant_id,
            'amount': str(transaction.amount),
            'currency': transaction.currency.upper(),
            'transaction_id': transaction.id
        }

    def process_payment(self, payment_data):
        """
        A diferencia de pasarelas de redirección, aquí el frontend manda el "Kushki Token"
        y nosotros procesamos el cargo (Charge).
        """
        token = payment_data.get('kushki_token')
        transaction_id = payment_data.get('transaction_id')
        
        if not token or not transaction_id:
            raise ValidationError("Kushki token or transaction ID missing")
            
        transaction = Transaction.objects.get(id=transaction_id)
        
        try:
            url = f"{self.base_url}/card/v1/charges"
            headers = {
                "Private-Merchant-Id": self.private_key,
                "Content-Type": "application/json"
            }
            data = {
                "token": token,
                "amount": {
                    "subtotalIva": 0,
                    "subtotalIva0": float(transaction.amount),
                    "ice": 0,
                    "iva": 0,
                    "currency": transaction.currency.upper()
                },
                "metadata": {
                    "transaction_id": str(transaction.id)
                },
                "fullResponse": True
            }
            
            response = requests.post(url, json=data, headers=headers)
            res_data = response.json()
            
            PaymentLog.objects.create(
                transaction=transaction,
                gateway_name='kushki',
                event_type="charge_attempt",
                payload=res_data
            )
            
            if response.status_code in [200, 201] and res_data.get('isSuccessful'):
                transaction.status = Transaction.Status.PAID
                transaction.gateway_transaction_id = res_data.get('ticketNumber')
                transaction.save()
                return {'success': True, 'data': res_data}
            else:
                transaction.status = Transaction.Status.FAILED
                transaction.save()
                return {'success': False, 'data': res_data, 'error': res_data.get('details', {}).get('responseText')}
                
        except Exception as e:
            raise ValidationError(detail=str(e))

    def verify_status(self, gateway_transaction_id):
        pass

    def refund_payment(self, transaction_id, amount):
        pass

    def handle_webhook(self, request_payload):
        # Para suscripciones o cobros asincronos
        return {'status': 'ignored'}
