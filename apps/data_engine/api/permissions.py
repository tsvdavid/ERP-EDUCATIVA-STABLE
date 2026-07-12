# apps/data_engine/api/permissions.py
"""Multi-Tenant Permissions for the Motor de Análisis y Carga (MAC) API Gateway.

Enforces strict tenant isolation across all endpoints. Prevents unauthorized cross-tenant
access or session hijacking between different institutions in ERP Eduka360.
"""

from typing import Any, Optional
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.data_engine.application.facade import MacApplicationFacade
from .exceptions import TenantIsolationViolation


class IsTenantAuthorized(permissions.BasePermission):
    """Enforces multi-tenant isolation on MAC API operations."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            # Allow DRF authentication layers or unauthenticated checks to fail normally via 401
            return False

        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True

        # Resolve target tenant_id from request body, query params, or session context
        target_tenant: Optional[str] = None
        if isinstance(request.data, dict):
            target_tenant = str(request.data.get("tenant_id", "") or "")
        if not target_tenant and hasattr(request, "query_params"):
            target_tenant = str(request.query_params.get("tenant_id", "") or "")

        # If no tenant_id found in data/params, check if pk / session_id in URL kwargs
        if not target_tenant and hasattr(view, "kwargs") and view.kwargs:
            session_id = str(view.kwargs.get("pk") or view.kwargs.get("session_id") or "")
            if session_id:
                try:
                    facade = MacApplicationFacade()
                    sess_dto = facade.get_session(session_id)
                    target_tenant = sess_dto.tenant_id
                except Exception:
                    pass

        if not target_tenant:
            # If endpoint doesn't require specific tenant scope or creates no isolation conflict
            return True

        # Check user permissions against target_tenant
        user_tenant = self._extract_user_tenant(request, user)
        if user_tenant and str(user_tenant) != str(target_tenant):
            raise TenantIsolationViolation(
                f"Cross-tenant access violation: user assigned to tenant '{user_tenant}' "
                f"cannot access resources for target tenant '{target_tenant}'."
            )

        return True

    def _extract_user_tenant(self, request: Request, user: Any) -> Optional[str]:
        """Attempt extracting the primary tenant or institution ID of the user."""
        # 1. Check direct attribute on user
        if hasattr(user, "tenant_id") and user.tenant_id:
            return str(user.tenant_id)
        if hasattr(user, "institution_id") and user.institution_id:
            return str(user.institution_id)
        if hasattr(user, "institution") and getattr(user.institution, "id", None):
            return str(user.institution.id)

        # 2. Check request tenant context set by middleware
        if hasattr(request, "tenant") and getattr(request.tenant, "id", None):
            return str(request.tenant.id)
        if hasattr(request, "tenant_id") and request.tenant_id:
            return str(request.tenant_id)

        # 3. Check X-Institution-Id header
        header_tenant = request.headers.get("X-Institution-Id") or request.META.get("HTTP_X_INSTITUTION_ID")
        if header_tenant:
            return str(header_tenant)

        return None
