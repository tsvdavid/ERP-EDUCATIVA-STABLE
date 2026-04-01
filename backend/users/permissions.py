from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to Admin users (Super Admin).
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsAdminOrLocalAdminUser(permissions.BasePermission):
    """
    Allows access to both Admin and Local Admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'LOCAL_ADMIN'])

class IsRectorUser(permissions.BasePermission):
    """
    Allows access only to Rector users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'RECTOR')

class IsTeacherUser(permissions.BasePermission):
    """
    Allows access only to Teacher users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'TEACHER')

class CanManageInstitution(permissions.BasePermission):
    """
    Admin: Full Access (Create, Read, Update, Delete)
    Rector: Update only (Read, Update)
    Others: No access (or Read only if specified, but usually strictly restricted)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if request.user.role in ['ADMIN', 'LOCAL_ADMIN'] or request.user.is_superuser:
            return True
        
        if request.user.role == 'RECTOR':
            # Rector cannot create or delete
            if view.action in ['create', 'destroy']:
                return False
            return True
            
        return False

class CanManageUser(permissions.BasePermission):
    def has_permission(self, request, view):
        # List/Create checks
        if not request.user.is_authenticated:
            return False
            
        if view.action in ['list', 'retrieve']:
            return True # Queryset handles visibility
            
        if view.action == 'create':
             # Teachers and Accountants cannot create users
             if request.user.role in ['TEACHER', 'ACCOUNTANT']:
                 return False
             return request.user.role in ['ADMIN', 'LOCAL_ADMIN', 'RECTOR'] or request.user.is_superuser
             
        # For update/destroy, need object permission
        return True

    def has_object_permission(self, request, view, obj):
        # Admin/Local Admin/Rector can manage all
        if request.user.role in ['ADMIN', 'LOCAL_ADMIN', 'RECTOR'] or request.user.is_superuser:
            return True
            
        # Teacher can UPDATE Students
        if request.user.role == 'TEACHER':
            if view.action in ['update', 'partial_update'] and obj.role == 'STUDENT':
                return True
            return False
            
        return False
