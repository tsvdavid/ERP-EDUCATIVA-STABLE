from rest_framework import routers
from django.urls import path, include
from .views import ProcedureTemplateViewSet, StudentRequestViewSet

router = routers.DefaultRouter()
router.register(r'templates', ProcedureTemplateViewSet, basename='procedure-templates')
router.register(r'requests', StudentRequestViewSet, basename='student-requests')

urlpatterns = [
    path('', include(router.urls)),
]
