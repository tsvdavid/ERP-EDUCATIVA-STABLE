from django.urls import path
from .views import BackupView, RestoreView, UserMaintenanceView, LogView, ResetView

urlpatterns = [
    path('backup/', BackupView.as_view(), name='backup'),
    path('restore/', RestoreView.as_view(), name='restore'),
    path('users/', UserMaintenanceView.as_view(), name='users'),
    path('log/', LogView.as_view(), name='log'),
    path('reset/', ResetView.as_view(), name='reset'),
]
