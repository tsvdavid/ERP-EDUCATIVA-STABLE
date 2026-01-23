from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentConceptViewSet, PaymentMethodViewSet, InvoiceViewSet, StudentAccountViewSet, ChargeViewSet

router = DefaultRouter()
router.register(r'concepts', PaymentConceptViewSet)
router.register(r'methods', PaymentMethodViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'accounts', StudentAccountViewSet)
router.register(r'charges', ChargeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
