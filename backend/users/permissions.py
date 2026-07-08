from rest_framework import permissions


def get_active_institution_id(request):
    tenant = getattr(request, 'tenant', None)
    if tenant and getattr(tenant, 'id', None):
        return tenant.id

    institution_id = getattr(request, 'institution_id', None)
    if institution_id:
        return institution_id

    user = getattr(request, 'user', None)
    if user and getattr(user, 'institution_id', None):
        return user.institution_id

    return None


def is_global_switched_to_institution(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return False
    if user.role != 'GLOBAL':
        return False

    active_institution_id = get_active_institution_id(request)
    if not active_institution_id:
        return False

    return getattr(user, 'institution_id', None) != active_institution_id

class IsAdminUser(permissions.BasePermission):
    """Acceso total: Administrador del sistema."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.role == 'ADMIN'
                or request.user.is_superuser
                or is_global_switched_to_institution(request)
            )
        )

class IsLocalAdminUser(permissions.BasePermission):
    """Acceso administrativo de la institución."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.role in ['ADMIN', 'LOCAL_ADMIN', 'RECTOR']
                or is_global_switched_to_institution(request)
            )
        )

class IsAccountantUser(permissions.BasePermission):
    """Perfil Contable/Tesorería."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ACCOUNTANT')

class IsTreasuryStaff(permissions.BasePermission):
    """Personal con acceso a caja y facturación."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.role in ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT', 'SECRETARY']
            or request.user.is_superuser
            or is_global_switched_to_institution(request)
        )

class IsAcademicStaff(permissions.BasePermission):
    """Personal con acceso a gestión académica."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.role in ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'SECRETARY']
            or request.user.is_superuser
            or is_global_switched_to_institution(request)
        )

class IsHealthStaff(permissions.BasePermission):
    """Personal del DECE y Médico."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.role in ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'DECE', 'MEDICO']
            or request.user.is_superuser
            or is_global_switched_to_institution(request)
        )

class CanManageInstitution(permissions.BasePermission):
    """Control sobre los datos de la institución."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in ['ADMIN', 'LOCAL_ADMIN'] or request.user.is_superuser:
            return True
        if is_global_switched_to_institution(request):
            return view.action not in ['create', 'destroy']
        if request.user.role == 'RECTOR':
            return view.action not in ['create', 'destroy']
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role in ['ADMIN', 'LOCAL_ADMIN']:
            return True
        if is_global_switched_to_institution(request):
            return getattr(obj, 'id', None) == get_active_institution_id(request)
        if user.role == 'RECTOR':
            return user.institution == obj
        return False

class CanManageUser(permissions.BasePermission):
    """Control sobre creación y edición de usuarios."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if view.action in ['list', 'retrieve']:
            return True
        if view.action == 'create':
            if request.user.role in ['TEACHER', 'ACCOUNTANT', 'PARENT', 'STUDENT']:
                return False
            return (
                request.user.role in ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'SECRETARY']
                or request.user.is_superuser
                or is_global_switched_to_institution(request)
            )
        return (
            request.user.role in ['ADMIN', 'LOCAL_ADMIN', 'RECTOR']
            or request.user.is_superuser
            or is_global_switched_to_institution(request)
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser or user.role in ['ADMIN', 'LOCAL_ADMIN', 'RECTOR']:
            return True
        if is_global_switched_to_institution(request):
            return getattr(obj, 'institution_id', None) == get_active_institution_id(request)
        # Los profesores pueden ver/editar ciertos datos de estudiantes asignados
        if user.role == 'TEACHER' and obj.role == 'STUDENT':
            return view.action in ['retrieve', 'update', 'partial_update']
        return False

class IsGlobalAdmin(permissions.BasePermission):
    """Acceso restringido a módulos en desarrollo."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == 'GLOBAL' or request.user.is_superuser)
        )
