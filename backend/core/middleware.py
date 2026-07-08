from django.db import connection
from django.core.exceptions import PermissionDenied
from users.models import Institution
from core.thread_context import set_current_tenant_id, clear_current_tenant

class TenantMiddleware:
    """
    Middleware de Hardening Multi-tenant.
    1. Establece request.tenant de forma segura y validada.
    2. Inyecta el ID del tenant en la sesión de Postgres para soporte de RLS.
    3. Almacena el context en ThreadLocal para el fail-safe del Manager.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def _set_rls_mode(self, mode):
        with connection.cursor() as cursor:
            cursor.execute("SET app.rls_mode = %s", [mode])

    def _set_tenant(self, tenant_id):
        with connection.cursor() as cursor:
            cursor.execute("SET app.current_tenant = %s", [str(tenant_id)])

    def _reset_rls_context(self):
        with connection.cursor() as cursor:
            cursor.execute("RESET app.current_tenant;")
            cursor.execute("RESET app.rls_mode;")

    def __call__(self, request):
        # ---------- Bypass total para rutas de autenticación ----------
        is_auth_route = request.path.startswith("/api/token/") or request.path.startswith(
            "/api/auth/"
        )
        if is_auth_route:
            # Auth requiere acceso global controlado para login/refresh/switch.
            request.tenant = None
            clear_current_tenant()
            self._set_rls_mode('global_admin')
            try:
                return self.get_response(request)
            finally:
                clear_current_tenant()
                self._reset_rls_context()

        # ---------- JWT authentication sólo para rutas protegidas ----------
        # Authentication is handled by Django's AuthenticationMiddleware; no JWT processing here.
        if hasattr(request, "user") and request.user.is_authenticated:
            pass

        tenant = None
        # Extraer institution_id del header
        header_institution = request.headers.get('X-Institution-ID')
        
        # JWT decoding is performed in JwtBootstrapMiddleware.
        # Here we only rely on request.institution_id (set by the bootstrap) and the X‑Institution‑ID header.
        token_institution = None  # not used in this middleware
        
        # Duplicate is_auth_route block removed (already handled above)
        # is_auth_route = request.path.startswith('/api/token/') or request.path.startswith('/api/auth/')  # redundant
        
        # if is_auth_route:  # redundant
            # En rutas de autenticación, no confiamos en el header (puede estar cacheado en el frontend de una sesión previa)  # redundant
            # Esto evita que authenticate() falle por RLS al buscar un superusuario (inst 1) con el header de otra inst (25)  # redundant
            # pass  # redundant
        # Resolve tenant ID with explicit priority:
        # 1️⃣ request.institution_id (set by JwtBootstrapMiddleware)
        # 2️⃣ X‑Institution‑ID header
        # 3️⃣ (optional) fallback to authenticated user’s institution
        if hasattr(request, 'institution_id') and request.institution_id:
            # already set by bootstrap
            pass
        elif header_institution:
            try:
                request.institution_id = int(header_institution)
            except (TypeError, ValueError):
                request.institution_id = None

        # else: no institution_id -> tenant will remain None

        # Asignar tenant object para RLS basado en institution_id
        if hasattr(request, 'institution_id') and request.institution_id:
            try:
                tenant = Institution.objects.get(id=request.institution_id)
            except Institution.DoesNotExist:
                pass
        
        request.tenant = tenant
            
        # HARDENING: Inyectar ID en la sesión de base de datos y ThreadLocal
        if tenant:
            # Check subscription status to block suspended users
            if not getattr(request.user, 'is_superuser', False):
                try:
                    sub = tenant.subscription
                    if sub.status == 'SUSPENDED':
                        # 1. API Enforcement
                        if request.path.startswith('/api/'):
                            exempt_api = ['/api/token/', '/api/auth/', '/api/subscriptions/my-billing/']
                            if not any(request.path.startswith(p) for p in exempt_api):
                                print(f"SUSPENDED ACCESS BLOCKED (API): user={request.user} institution={tenant.name} path={request.path}")
                                from django.http import JsonResponse
                                return JsonResponse({
                                    "code": "SUBSCRIPTION_SUSPENDED",
                                    "institution_name": tenant.name,
                                    "status": "SUSPENDED"
                                }, status=403)
                        
                        # 2. Dashboard Enforcement (Frontend)
                        elif request.path.startswith('/dashboard'):
                            exempt_web = ['/dashboard/settings/billing']
                            if not any(request.path.startswith(p) for p in exempt_web):
                                print(f"SUSPENDED ACCESS BLOCKED (WEB): user={request.user} institution={tenant.name} path={request.path}")
                                from django.shortcuts import redirect
                                return redirect('/subscription-suspended')
                except Exception:
                    pass

            set_current_tenant_id(tenant.id)
            self._set_rls_mode('tenant')
            self._set_tenant(tenant.id)
        else:
            # No tenant válido, limpiamos contexto sin forzar ID 0
            clear_current_tenant()
            self._set_rls_mode('tenant')

        try:
            response = self.get_response(request)
            if hasattr(response, 'render') and callable(response.render):
                response.render()
        except PermissionDenied as e:
            raise e
        except Exception as e:
            raise e
        finally:
            clear_current_tenant()
            self._reset_rls_context()
            
        return response
