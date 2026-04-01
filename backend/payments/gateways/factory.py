from django.core.exceptions import ImproperlyConfigured
from payments.gateways.stripe import StripeGateway
from payments.gateways.paypal import PayPalGateway
from payments.gateways.mercadopago import MercadoPagoGateway
from payments.gateways.payphone import PayPhoneGateway
from payments.gateways.kushki import KushkiGateway
from payments.gateways.datafast import DatafastGateway
from payments.gateways.bank_transfer import BankTransferGateway

class PaymentGatewayFactory:
    """
    Desacopla a todo el sistema de una pasarela específica. 
    Llama a esta fábrica pasándole el "nombre" y te retorna su controlador.
    """
    
    _gateways = {
        'stripe': StripeGateway,
        'paypal': PayPalGateway,
        'mercadopago': MercadoPagoGateway,
        'payphone': PayPhoneGateway,
        'kushki': KushkiGateway,
        'datafast': DatafastGateway,
        'bank_transfer': BankTransferGateway,
    }

    @classmethod
    def get_gateway(cls, gateway_name, institution=None):
        gateway_class = cls._gateways.get(gateway_name.lower())
        
        if not gateway_class:
            raise ImproperlyConfigured(f"El método de pago '{gateway_name}' no está registrado o configurado.")
            
        return gateway_class(institution=institution)
