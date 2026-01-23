from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PolicyVersionViewSet, 
    ConsentRecordViewSet, 
    ARCORequestViewSet,
    TreatmentActivityViewSet,
    DataBreachViewSet
)

router = DefaultRouter()
router.register(r'policies', PolicyVersionViewSet)
router.register(r'consents', ConsentRecordViewSet, basename='consent')
router.register(r'arco', ARCORequestViewSet, basename='arco')
router.register(r'rat', TreatmentActivityViewSet, basename='rat')
router.register(r'breaches', DataBreachViewSet, basename='breach')

urlpatterns = [
    path('', include(router.urls)),
]
