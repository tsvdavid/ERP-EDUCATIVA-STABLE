from django.shortcuts import get_object_or_404
from users.models import Institution

def get_tenant_from_request(request):
    """
    Helper to extract the current institution from the request.
    Priority:
    1. request.tenant (set by TenantMiddleware)
    """
    if hasattr(request, 'tenant') and request.tenant:
        return request.tenant

    return None

def get_tenant_or_404(request):
    """
    Strict helper that raises 404 if no tenant context is found.
    """
    tenant = get_tenant_from_request(request)
    if not tenant:
        from rest_framework.exceptions import NotFound
        raise NotFound("No se pudo determinar el contexto de la institución para esta petición.")
    return tenant
