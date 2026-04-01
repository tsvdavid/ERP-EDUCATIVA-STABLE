import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') 

import django
django.setup()

from users.models import User, Institution
from payments.models import PaymentGatewayConfig, Transaction
from payments.gateways.factory import PaymentGatewayFactory

def run():
    # Setup Data
    institution, _ = Institution.objects.get_or_create(name='Test Institucion', defaults={'domain': 'test.com'})
    
    # Setup Gateway config
    PaymentGatewayConfig.objects.update_or_create(
        institution=institution,
        gateway_name='stripe',
        defaults={
            'is_active': True,
            'is_test_mode': True,
            'credentials': {'secret_key': 'sk_test_123', 'webhook_secret': 'whsec_123'}
        }
    )
    
    # Test Stripe Gateway
    stripe_gw = PaymentGatewayFactory.get_gateway('stripe', institution=institution)
    print("Stripe Webhook Secret:", stripe_gw.webhook_secret)
    import stripe
    print("Stripe API Key:", stripe.api_key) 
    
    # Test MercadoPago Gateway
    PaymentGatewayConfig.objects.update_or_create(
        institution=institution,
        gateway_name='mercadopago',
        defaults={
            'is_active': True,
            'is_test_mode': True,
            'credentials': {'access_token': 'TEST-123'}
        }
    )
    mp_gw = PaymentGatewayFactory.get_gateway('mercadopago', institution=institution)
    print("MP Access Token:", mp_gw.access_token) 

if __name__ == '__main__':
    run()
