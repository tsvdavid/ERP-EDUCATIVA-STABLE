from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InstitutionViewSet, UserViewSet, CustomTokenObtainPairView, SwitchInstitutionView

router = DefaultRouter()
router.register(r'institutions', InstitutionViewSet)
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('token/switch/', SwitchInstitutionView.as_view(), name='token_switch'),
    path('', include(router.urls)),
]
