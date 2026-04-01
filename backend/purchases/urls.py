from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupplierViewSet, PurchaseInvoiceViewSet, PurchaseCreditNoteViewSet, PurchaseDebitNoteViewSet, PurchaseLiquidationViewSet

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'invoices', PurchaseInvoiceViewSet, basename='invoice')
router.register(r'credit-notes', PurchaseCreditNoteViewSet, basename='credit-note')
router.register(r'debit-notes', PurchaseDebitNoteViewSet, basename='debit-note')
router.register(r'liquidations', PurchaseLiquidationViewSet, basename='liquidation')

urlpatterns = [
    path('', include(router.urls)),
]
