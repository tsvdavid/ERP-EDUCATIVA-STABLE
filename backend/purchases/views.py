from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Supplier, PurchaseInvoice
from .serializers import SupplierSerializer, PurchaseInvoiceSerializer

class SupplierViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Supplier.objects.filter(institution=self.request.user.institution)

    def perform_create(self, serializer):
        serializer.save(institution=self.request.user.institution)

class PurchaseInvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PurchaseInvoice.objects.filter(institution=self.request.user.institution).select_related(
            'supplier', 'withholding'
        ).prefetch_related(
            'items', 'items__expense_account'
        ).order_by('-issue_date')

    def perform_create(self, serializer):
        serializer.save(
            institution=self.request.user.institution,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status == 'VALIDATED':
            return Response({'error': 'La factura ya está validada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        invoice.status = 'VALIDATED'
        invoice.save() # Signals will handle accounting
        
        return Response({'status': 'validated'})
