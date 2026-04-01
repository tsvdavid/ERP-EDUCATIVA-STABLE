from abc import ABC, abstractmethod

class BasePaymentGateway(ABC):
    """
    Capa de Abstracción Universal para Proveedores de Pago.
    Cualquier pasarela nueva (Stripe, Paypal, PayPhone) DEBE heredar de esta clase
    y cumplir con este contrato para asegurar la interoperabilidad con el ERP.
    """

    @abstractmethod
    def create_payment_intent(self, transaction):
        """
        Inicializa un intento de pago en el proveedor.
        Retorna la URL de checkout o un Client Token.
        """
        pass

    @abstractmethod
    def process_payment(self, payment_data):
        """
        Procesa el pago directo usando los datos recibidos (ej: token de tarjeta).
        Retorna un diccionario indicando success=True/False y la data interna.
        """
        pass

    @abstractmethod
    def verify_status(self, gateway_transaction_id):
        """
        Consulta proactivamente al proveedor si una transacción dada está pagada o no.
        """
        pass

    @abstractmethod
    def refund_payment(self, transaction_id, amount):
        """
        Ejecuta la devolución de dinero sobre una transacción dada.
        """
        pass

    @abstractmethod
    def handle_webhook(self, request_payload):
        """
        Recepta el webhook asíncrono enviado por el proveedor para notificar cobros,
        y traduce dicho payload en la actualización del Transaction() y cierre de facturas.
        """
        pass
