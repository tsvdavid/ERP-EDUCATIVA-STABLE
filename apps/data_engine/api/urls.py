# apps/data_engine/api/urls.py
"""URL routing configuration for the MAC API Gateway.

Registers REST viewsets and individual API endpoints under the `/api/data-engine/` namespace.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ImportSessionViewSet,
    PreviewAPIView,
    ValidationAPIView,
)

router = DefaultRouter()
router.register(r"sessions", ImportSessionViewSet, basename="mac-session")

urlpatterns = [
    path("", include(router.urls)),
    path("validate/", ValidationAPIView.as_view(), name="mac-validate"),
    path("preview/", PreviewAPIView.as_view(), name="mac-preview"),
]
