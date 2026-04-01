from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments.views import PaymentViewSet, WebhookView, PaymentGatewayConfigViewSet

router = DefaultRouter()
router.register(r'payment-gateway-configs', PaymentGatewayConfigViewSet, basename='payment_gateway_configs')
router.register(r'config', PaymentGatewayConfigViewSet, basename='payment_config')
# Empty prefix for transactions so that checkout/ maps directly to /api/payments/checkout/
router.register(r'', PaymentViewSet, basename='payment_transactions')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/<str:gateway_name>/', WebhookView.as_view(), name='payment_webhook'),
]
