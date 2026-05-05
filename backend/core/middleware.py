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

    def __call__(self, request):
        # DRF Support: Si no hay usuario, intentamos JWT manual
        if not request.user or not request.user.is_authenticated:
            from rest_framework_simplejwt.authentication import JWTAuthentication
            try:
                auth = JWTAuthentication().authenticate(request)
                if auth:
                    request.user = auth[0]
            except:
                pass

        tenant = None
        # Extraer institution_id del header
        header_institution = request.headers.get('X-Institution-ID')
        
        # Extraer institution_id del token (si existe)
        token_institution = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                access_token = AccessToken(token)
                token_institution = access_token.get('institution')
            except:
                pass
        
        # REGLA: Eximir rutas públicas de autenticación del header
        is_auth_route = request.path.startswith('/api/token/') or request.path.startswith('/api/auth/')
        
        if is_auth_route:
            # En rutas de autenticación, no confiamos en el header (puede estar cacheado en el frontend de una sesión previa)
            # Esto evita que authenticate() falle por RLS al buscar un superusuario (inst 1) con el header de otra inst (25)
            pass
        elif hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
            # Superusuario: el header prevalece, no validamos contra token
            if header_institution:
                request.institution_id = int(header_institution)
            elif token_institution:
                request.institution_id = token_institution
        else:
            # Usuario normal: el header debe coincidir con el token
            if header_institution and token_institution:
                if str(header_institution) != str(token_institution):
                    from django.http import HttpResponseForbidden
                    return HttpResponseForbidden("Tenant mismatch")
                request.institution_id = int(header_institution)
            elif token_institution:
                request.institution_id = token_institution
            elif header_institution:
                request.institution_id = int(header_institution)

        # Asignar tenant object para RLS basado en institution_id
        if hasattr(request, 'institution_id') and request.institution_id:
            try:
                tenant = Institution.objects.get(id=request.institution_id)
            except Institution.DoesNotExist:
                pass
        
        if not tenant and hasattr(request.user, 'institution'):
            tenant = request.user.institution
            
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
            with connection.cursor() as cursor:
                cursor.execute(f"SET app.current_tenant = '{tenant.id}';")
        else:
            set_current_tenant_id(0) # Contexto bloqueado
            with connection.cursor() as cursor:
                cursor.execute("SET app.current_tenant = '0';")

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
            with connection.cursor() as cursor:
                cursor.execute("RESET app.current_tenant;")
            
        return response
