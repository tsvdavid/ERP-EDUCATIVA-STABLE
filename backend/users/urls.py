from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InstitutionViewSet, UserViewSet

router = DefaultRouter()
router.register(r'institutions', InstitutionViewSet)
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
