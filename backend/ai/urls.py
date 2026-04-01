from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIConfigViewSet, assistantViewSet

router = DefaultRouter()
router.register(r'config', AIConfigViewSet, basename='ai-config')
router.register(r'assistant', assistantViewSet, basename='ai-assistant')

urlpatterns = [
    path('', include(router.urls)),
]
