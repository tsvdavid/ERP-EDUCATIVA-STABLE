import requests
import json
import base64
import hashlib
import uuid
from datetime import datetime
from django.conf import settings
from rest_framework.exceptions import ValidationError
from payments.gateways.base import BasePaymentGateway
from payments.models import Transaction, PaymentLog

class DatafastGateway(BasePaymentGateway):
    """
    Integración con Datafast (Placetopay / Nuvei).
    """
    def __init__(self):
        self.login = getattr(settings, 'DATAFAST_LOGIN', 'placeholder_login')
        self.tran_key = getattr(settings, 'DATAFAST_TRANKEY', 'placeholder_trankey')
        self.base_url = getattr(settings, 'DATAFAST_URL', 'https://test.placetopay.ec/redirection')

    def _generate_auth(self):
        nonce = uuid.uuid4().hex
        seed = datetime.now().isoformat()
        
        # tranKey + seed + nonce
        raw_hash = f"{nonce}{seed}{self.tran_key}".encode('utf-8')
        digest = hashlib.sha256(raw_hash).digest()
        
        encoded_nonce = base64.b64encode(nonce.encode('utf-8')).decode('utf-8')
        encoded_hash = base64.b64encode(digest).decode('utf-8')
        
        return {
            "login": self.login,
            "tranKey": encoded_hash,
            "nonce": encoded_nonce,
            "seed": seed
        }

    def create_payment_intent(self, transaction):
        """
        Crea una solicitud de sesión en Placetopay.
        Retorna la processUrl.
        """
        try:
            url = f"{self.base_url}/api/session"
            payload = {
                "auth": self._generate_auth(),
                "payment": {
                    "reference": str(transaction.id),
                    "description": transaction.description or f"Factura {transaction.reference_id}",
                    "amount": {
                        "currency": transaction.currency.upper(),
                        "total": float(transaction.amount)
                    }
                },
                "expiration": datetime.now().strftime("%Y-%m-%dT%H:%M:%S-05:00"), # Needs Proper Future Offset normally, simplified here
                "returnUrl": getattr(settings, 'DATAFAST_RETURN_URL', 'http://localhost:3000/payments/datafast/return/' + str(transaction.id)),
                "ipAddress": "127.0.0.1", # Ideal obtener del request original
                "userAgent": "ERP-EDUCATIVA/1.0"
            }
            
            # Simple hack for expiration +30 min
            import datetime as dt
            payload["expiration"] = (dt.datetime.now() + dt.timedelta(minutes=30)).isoformat()

            response = requests.post(url, json=payload)
            res_data = response.json()
            
            if response.status_code == 200 and res_data.get('status', {}).get('status') == 'OK':
                request_id = res_data.get('requestId')
                process_url = res_data.get('processUrl')
                
                transaction.gateway_transaction_id = str(request_id)
                transaction.save(update_fields=['gateway_transaction_id'])
                
                return {
                    'request_id': request_id,
                    'process_url': process_url
                }
            else:
                raise ValidationError(f"Error en Datafast: {res_data}")

        except Exception as e:
            raise ValidationError(detail=str(e))

    def process_payment(self, payment_data):
        pass

    def verify_status(self, gateway_transaction_id):
        pass

    def refund_payment(self, transaction_id, amount):
        pass

    def handle_webhook(self, request_payload):
        # Placetopay maneja notificaciones webhook
        try:
             # Basic implementation outline
             status = request_payload.get('status', {}).get('status')
             request_id = request_payload.get('requestId')
             reference = request_payload.get('reference')
             
             transaction = Transaction.objects.filter(gateway_transaction_id=str(request_id)).first()
             if transaction:
                  PaymentLog.objects.create(transaction=transaction, gateway_name='datafast', event_type=status, payload=request_payload)
                  if status == 'APPROVED':
                       transaction.status = Transaction.Status.PAID
                       transaction.save()
                  elif status == 'REJECTED':
                       transaction.status = Transaction.Status.FAILED
                       transaction.save()
                       
             return {'status': 'success'}
        except Exception:
             return {'status': 'error'}
