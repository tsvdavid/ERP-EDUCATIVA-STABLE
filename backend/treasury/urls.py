from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentConceptViewSet, PaymentMethodViewSet, InvoiceViewSet, 
    StudentAccountViewSet, ChargeViewSet, CreditNoteViewSet, DebitNoteViewSet
)

router = DefaultRouter()
router.register(r'concepts', PaymentConceptViewSet)
router.register(r'methods', PaymentMethodViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'accounts', StudentAccountViewSet)
router.register(r'charges', ChargeViewSet)
router.register(r'credit-notes', CreditNoteViewSet, basename='credit-note')
router.register(r'debit-notes', DebitNoteViewSet, basename='debit-note')

urlpatterns = [
    path('', include(router.urls)),
]
