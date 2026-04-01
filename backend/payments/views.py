import json
import logging
from django.db import transaction as db_transaction
from rest_framework import viewsets, views, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from payments.models import Transaction, PaymentLog, PaymentGatewayConfig
from payments.serializers import TransactionSerializer, CheckoutSerializer, PaymentGatewayConfigSerializer
from payments.gateways.factory import PaymentGatewayFactory

logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if hasattr(self, 'action') and self.action == 'verify_transfer' and getattr(self.request.user, 'role', '') == 'ADMIN':
            return Transaction.objects.all()
        return Transaction.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], serializer_class=CheckoutSerializer)
    def checkout(self, request):
        """
        Inicia un intento de pago, centralizado y abstracto.
        Delegará a la clase StripeGateway / PayphoneGateway usando Factory.
        """
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        gateway_name = data.get('gateway_name')
        
        try:
            # 1. Crear transacción PENDIENTE (o en VERIFICACIÓN si es transferencia)
            with db_transaction.atomic():
                status_to_save = Transaction.Status.PENDING
                if gateway_name == 'bank_transfer':
                    status_to_save = Transaction.Status.VERIFYING
                    
                txn = Transaction.objects.create(
                    user=request.user,
                    amount=data['amount'],
                    currency=data['currency'],
                    status=status_to_save,
                    gateway_name=gateway_name,
                    reference_id=data.get('reference_id', ''),
                    description=data.get('description', ''),
                    voucher_file=request.FILES.get('voucher_file') or request.data.get('voucher_file')
                )
            
            # 2. Obtener el adaptador
            institution = getattr(request.user, 'institution', None)
            gateway = PaymentGatewayFactory.get_gateway(gateway_name, institution=institution)
            
            # 3. Solicitar URL o Token al proveedor
            result = gateway.create_payment_intent(txn)
            
            return Response({
                'transaction_id': txn.id,
                'gateway_name': gateway_name,
                'checkout_data': result # URL, token, client_secret...
            })
            
        except Exception as e:
            logger.exception("Error en Checkout Payment")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def pending_transfers(self, request):
        """
        Retorna transacciones en estado VERIFYING para que sean aprobadas/rechazadas por Admin/Tesorería.
        """
        txns = Transaction.objects.filter(status=Transaction.Status.VERIFYING, gateway_name='bank_transfer')
        serializer = self.get_serializer(txns, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def verify_transfer(self, request, pk=None):
        """
        Aprueba o rechaza una transferencia. payload: { "action": "approve" | "reject" }
        """
        txn = self.get_object()
        if txn.status != Transaction.Status.VERIFYING:
            return Response({"error": "Transacción no está en verificación."}, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get('action')
        
        with db_transaction.atomic():
            if action == 'approve':
                txn.status = Transaction.Status.PAID
                txn.save()
                PaymentLog.objects.create(transaction=txn, gateway_name=txn.gateway_name, event_type="manual_approval", payload={"user_id": request.user.id})
                
                # Procesar la factura si tenemos reference_id
                if txn.reference_id and txn.reference_id.isdigit():
                    from treasury.models import Charge, PaymentMethod, PaymentConcept, Invoice, InvoiceDetail, Payment
                    try:
                        charge = Charge.objects.get(id=txn.reference_id)
                        if not charge.is_paid:
                            student = charge.student
                            
                            # Comprobar si ya existe una factura para este cobro (por ej. si se creó como 'Pendiente' en Facturación)
                            detail = InvoiceDetail.objects.filter(charge=charge).first()
                            
                            if detail:
                                invoice = detail.invoice
                                Payment.objects.create(
                                    invoice=invoice,
                                    amount_paid=invoice.total,
                                    verified=True
                                )
                                charge.is_paid = True
                                charge.save()
                            else:
                                # Generar Factura Nueva
                                pm = PaymentMethod.objects.filter(institution=student.institution).first()
                                
                                last_invoice = Invoice.objects.filter(institution=student.institution).order_by('-id').first()
                                est = "001"
                                pto = "001"
                                seq = 1
                                if last_invoice:
                                    parts = last_invoice.number.split('-')
                                    if len(parts) == 3:
                                        try: seq = int(parts[2]) + 1
                                        except: pass
                                    elif last_invoice.number.isdigit():
                                        seq = int(last_invoice.number) + 1
                                invoice_number = f"{est}-{pto}-{seq:09d}"

                                invoice = Invoice.objects.create(
                                    institution=student.institution,
                                    student=student,
                                    number=invoice_number,
                                    status='ISSUED',
                                    client_name=f"{student.first_name} {student.last_name}",
                                    client_ruc=student.cedula or '9999999999',
                                    payment_method=pm,
                                    created_by=request.user
                                )
                                
                                subtotal = charge.amount
                                iva = subtotal * charge.concept.iva_rate
                                
                                InvoiceDetail.objects.create(
                                    invoice=invoice,
                                    concept=charge.concept,
                                    quantity=1,
                                    unit_price=subtotal,
                                    subtotal=subtotal,
                                    charge=charge
                                )
                                
                                invoice.subtotal_0 = subtotal if charge.concept.iva_rate == 0 else 0
                                invoice.subtotal_15 = subtotal if charge.concept.iva_rate > 0 else 0
                                invoice.iva_total = iva
                                invoice.total = subtotal + iva
                                invoice.save()
                                
                                Payment.objects.create(
                                    invoice=invoice,
                                    amount_paid=invoice.total,
                                    verified=True
                                )
                                
                                charge.is_paid = True
                                charge.save()
                    except Exception as e:
                        logger.error(f"Error generando factura para txn {txn.id}: {e}")

                return Response({"status": "Aprobado", "transaction_id": txn.id})
            elif action == 'reject':
                txn.status = Transaction.Status.REJECTED if hasattr(Transaction.Status, 'REJECTED') else Transaction.Status.FAILED
                txn.save()
                PaymentLog.objects.create(transaction=txn, gateway_name=txn.gateway_name, event_type="manual_rejection", payload={"user_id": request.user.id})
                return Response({"status": "Rechazado", "transaction_id": txn.id})
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAdminUser])
    def delete_transfer(self, request, pk=None):
        """
        Elimina un registro de transferencia.
        """
        txn = self.get_object()
        if txn.status != Transaction.Status.VERIFYING:
            return Response({"error": "Solo se pueden eliminar transferencias en verificación."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Eliminar archivo si existe
        if txn.voucher_file:
            txn.voucher_file.delete()
        txn.delete()
        return Response({"status": "Transferencia eliminada correctamente.", "transaction_id": pk}, status=status.HTTP_204_NO_CONTENT)

class WebhookView(views.APIView):
    authentication_classes = [] # El webhook viene del proveedor sin token del sistema
    permission_classes = [] 

    def post(self, request, gateway_name):
        """
        Escucha universal de notificaciones de pago (asíncrono).
        """
        try:
            institution_id = request.query_params.get('institution_id')
            institution = None
            if institution_id:
                # Import format here to avoid circular imports if users app loads after payments
                from users.models import Institution
                institution = Institution.objects.filter(id=institution_id).first()
                
            gateway = PaymentGatewayFactory.get_gateway(gateway_name, institution=institution)
            payload = request.data
            
            # Delega el análisis al Gateway correcto
            result = gateway.handle_webhook(payload)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error procesando Webhook de {gateway_name}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentGatewayConfigViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentGatewayConfigSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Todos los autenticados pueden ver la lista activa
        if getattr(self.request.user, 'role', '') == 'ADMIN':
            return PaymentGatewayConfig.objects.filter(
                institution=getattr(self.request.user, 'institution', None)
            )
        else:
            return PaymentGatewayConfig.objects.filter(
                institution=getattr(self.request.user, 'institution', None),
                is_active=True
            )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        if getattr(request.user, 'role', '') != 'ADMIN':
            # Filtrar credenciales, dejando solo campos bancarios si es bank_transfer
            for item in data:
                safe_credentials = {}
                if item.get('gateway_name') == 'bank_transfer' and 'credentials' in item:
                    safe_credentials['bank_name'] = item['credentials'].get('bank_name', '')
                    safe_credentials['account_type'] = item['credentials'].get('account_type', '')
                    safe_credentials['owner_id'] = item['credentials'].get('owner_id', '')
                    safe_credentials['email'] = item['credentials'].get('email', '')
                item['credentials'] = safe_credentials
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        if getattr(request.user, 'role', '') != 'ADMIN':
            safe_credentials = {}
            if data.get('gateway_name') == 'bank_transfer' and 'credentials' in data:
                safe_credentials['bank_name'] = data['credentials'].get('bank_name', '')
                safe_credentials['account_type'] = data['credentials'].get('account_type', '')
                safe_credentials['owner_id'] = data['credentials'].get('owner_id', '')
                safe_credentials['email'] = data['credentials'].get('email', '')
            data['credentials'] = safe_credentials
        return Response(data)

    def get_permissions(self):
        # Restringir creación, actualización y borrado a Administradores
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            class IsAdminRule(permissions.BasePermission):
                def has_permission(self, request, view):
                    return request.user.is_authenticated and getattr(request.user, 'role', '') == 'ADMIN'
            return [IsAdminRule()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(institution=getattr(self.request.user, 'institution', None))
