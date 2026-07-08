from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionAdminViewSet, MySubscriptionViewSet, ObservabilityViewSet, PlanViewSet, GlobalSettingsViewSet

router = DefaultRouter()
router.register(r'plans', PlanViewSet, basename='subscription-plans')
router.register(r'admin', SubscriptionAdminViewSet, basename='subscription-admin')
router.register(r'global-settings', GlobalSettingsViewSet, basename='global-settings')
router.register(r'observability', ObservabilityViewSet, basename='subscription-observability')
router.register(r'my-billing', MySubscriptionViewSet, basename='my-subscription')

urlpatterns = [
    path('plans/modules-catalog', PlanViewSet.as_view({'get': 'modules_catalog'})),
    path('plans/modules-catalog/', PlanViewSet.as_view({'get': 'modules_catalog'}), name='subscription-plans-modules-catalog-explicit'),
    path('', include(router.urls)),
]
