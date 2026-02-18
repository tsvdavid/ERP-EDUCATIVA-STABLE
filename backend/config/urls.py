from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from users.views import CustomTokenObtainPairView

def root_view(request):
    log_content = "Log not found"
    try:
        with open('/tmp/login_debug.log', 'r') as f:
            log_content = f.read()
    except Exception as e:
        log_content = str(e)
    return JsonResponse({"status": "ERP Backend Operating", "debug_log": log_content})

urlpatterns = [
    path('', root_view),
    path('admin/', admin.site.urls),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/', include('users.urls')),
    path('api/academic/', include('academic.urls')),
    path('api/communication/', include('communication.urls')),
    path('api/treasury/', include('treasury.urls')),
    path('api/accounting/', include('accounting.urls')),
    path('api/purchases/', include('purchases.urls')),
    path('api/helpdesk/', include('helpdesk.urls')),
    path('api/privacy/', include('privacy.urls')),
    path('api/maintenance/', include('maintenance.urls')),

]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
