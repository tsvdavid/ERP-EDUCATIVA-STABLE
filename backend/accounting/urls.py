from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, JournalEntryViewSet, ReportViewSet, BankViewSet, BankAccountViewSet, FixedAssetViewSet, FiscalYearViewSet

router = DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'entries', JournalEntryViewSet)
router.register(r'reports', ReportViewSet, basename='reports')
router.register(r'banks', BankViewSet)
router.register(r'bank-accounts', BankAccountViewSet)
router.register(r'fixed-assets', FixedAssetViewSet)
router.register(r'fiscal-years', FiscalYearViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
