from payments.gateways.base import BasePaymentGateway
from payments.models import Transaction, PaymentGatewayConfig

class BankTransferGateway(BasePaymentGateway):
    """
    Gateway dummy para manejar el inicio de pagos por transferencia bancaria.
    No se comunica con ninguna API externa, solo delega a la creación manual de la transacción
    y recibe el voucher de deposito en la base de datos local.
    """
    def __init__(self, institution=None):
        self.institution = institution
        # Las instrucciones de depósito (banco, número de cuenta, etc)
        # se obtienen de la base de datos, del registro "bank_transfer"
        config = PaymentGatewayConfig.objects.filter(
            institution=institution, 
            gateway_name='bank_transfer',
            is_active=True
        ).first()

        self.account_instructions = ""
        if config and config.credentials:
            self.account_instructions = config.credentials.get('instructions', '')

    def create_payment_intent(self, transaction: Transaction) -> dict:
        """
        Para transferencias, no hay un 'intent' remoto. 
        Retorna las instrucciones de la cuenta para que el usuario pueda depositar si es necesario 
        y confirma la recepción del comprobante de depósito en el frontend.
        """
        # Validar si subieron voucher
        if not transaction.voucher_file:
            raise ValueError("Por favor adjunta el comprobante (voucher) de la transferencia bancaria.")

        return {
            "status": "verifying",
            "message": "Comprobante recibido satisfactoriamente, esperando confirmación del área contable.",
            "instructions": self.account_instructions
        }

    def handle_webhook(self, payload: dict) -> dict:
        """
        No hay webhooks remotos en transferencias manuales.
        """
        return {"status": "ignored"}

    def process_payment(self, amount: float, currency: str, source: str, **kwargs) -> dict:
        """
        Procesa el pago directamente (no aplica para transferencias manuales).
        """
        raise NotImplementedError("Bank transfer does not support direct processing.")

    def refund_payment(self, transaction: Transaction) -> dict:
        """
        Reembolsa un pago.
        """
        raise NotImplementedError("Bank transfer does not support automated refunds.")

    def verify_status(self, transaction: Transaction) -> dict:
        """
        Verifica el estado del pago. Para transferencias manuales simplemente retorna el estado actual de la BD.
        """
        return {"status": transaction.status, "message": "Manual verification required."}
