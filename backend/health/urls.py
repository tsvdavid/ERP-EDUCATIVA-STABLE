from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MedicalRecordViewSet, MedicalVisitViewSet,
    DeceRecordViewSet, DeceVisitViewSet,
    BehaviorRecordViewSet, BehaviorCaseViewSet,
    CaseFollowUpViewSet, StudentRiskProfileViewSet,
    AlertRuleViewSet,
)

router = DefaultRouter()
router.register(r'medical-records',       MedicalRecordViewSet)
router.register(r'medical-visits',        MedicalVisitViewSet)
router.register(r'dece-records',          DeceRecordViewSet)
router.register(r'dece-visits',           DeceVisitViewSet)
router.register(r'behavior-records',      BehaviorRecordViewSet)
router.register(r'behavior-cases',        BehaviorCaseViewSet)
router.register(r'case-follow-ups',       CaseFollowUpViewSet)
router.register(r'student-risk-profiles', StudentRiskProfileViewSet)
router.register(r'alert-rules',           AlertRuleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
