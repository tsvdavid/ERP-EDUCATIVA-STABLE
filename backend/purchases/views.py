from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Supplier, PurchaseInvoice, PurchaseCreditNote, PurchaseDebitNote, PurchaseLiquidation
from .serializers import SupplierSerializer, PurchaseInvoiceSerializer, PurchaseCreditNoteSerializer, PurchaseDebitNoteSerializer, PurchaseLiquidationSerializer

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

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status == 'CANCELLED':
            return Response({'error': 'La factura ya está anulada.'}, status=status.HTTP_400_BAD_REQUEST)
            
        invoice.status = 'CANCELLED'
        # Optional: reverse accounting via signals or manually here
        invoice.save()
        
        return Response({'status': 'cancelled'})

class PurchaseCreditNoteViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseCreditNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PurchaseCreditNote.objects.filter(institution=self.request.user.institution).select_related(
            'invoice', 'invoice__supplier'
        ).order_by('-issue_date')

    def perform_create(self, serializer):
        serializer.save(
            institution=self.request.user.institution,
            created_by=self.request.user
        )

class PurchaseDebitNoteViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseDebitNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PurchaseDebitNote.objects.filter(institution=self.request.user.institution).select_related(
            'invoice', 'invoice__supplier'
        ).order_by('-issue_date')

    def perform_create(self, serializer):
        serializer.save(
            institution=self.request.user.institution,
            created_by=self.request.user
        )

class PurchaseLiquidationViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseLiquidationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PurchaseLiquidation.objects.filter(institution=self.request.user.institution).select_related(
            'supplier'
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
        liquidation = self.get_object()
        if liquidation.status == 'VALIDATED':
            return Response({'error': 'La liquidación ya está validada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        liquidation.status = 'VALIDATED'
        liquidation.save()
        
        return Response({'status': 'validated'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        liquidation = self.get_object()
        if liquidation.status == 'CANCELLED':
            return Response({'error': 'La liquidación ya está anulada.'}, status=status.HTTP_400_BAD_REQUEST)
            
        liquidation.status = 'CANCELLED'
        liquidation.save()
        
        return Response({'status': 'cancelled'})
