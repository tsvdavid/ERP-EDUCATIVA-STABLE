from django.contrib.auth.models import UserManager
from django.contrib.auth.base_user import BaseUserManager
from django.db.models import Q
from core.thread_context import get_current_tenant_id

class TenantUserManager(UserManager):
    """Manager for the custom User model that supports multi‑tenant isolation.
    Inherits Django's built‑in UserManager (provides create_user/create_superuser)
    and adds the tenant‑aware queryset filtering used by the rest of the app.
    """

    def get_queryset(self):
        # Start from the standard UserManager queryset
        qs = super().get_queryset()
        tenant_id = get_current_tenant_id()
        if tenant_id and tenant_id != 0:
            # Allow global superusers to be visible across tenants
            if hasattr(self.model, 'is_superuser'):
                return qs.filter(Q(institution_id=tenant_id) | Q(is_superuser=True))
            return qs.filter(institution_id=tenant_id)
        return qs.none()

    def global_queryset(self):
        return super().get_queryset()

    def unscoped(self):
        return self.global_queryset()

    def get_by_natural_key(self, username):
        tenant_id = get_current_tenant_id()
        if tenant_id and tenant_id != 0:
            return self.get_queryset().get(**{self.model.USERNAME_FIELD: username})
        return self.global_queryset().get(**{self.model.USERNAME_FIELD: username})

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create a superuser with role validation.
        The role is checked against the User model's Role TextChoices.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'GLOBAL')
        # ---- role validation ----
        role_value = extra_fields.get('role')
        if hasattr(self.model, 'Role'):
            valid_roles = [choice.value for choice in self.model.Role]
            if role_value not in valid_roles:
                raise ValueError(
                    f"Invalid role '{role_value}' for superuser. Valid roles: {valid_roles}"
                )
        return super().create_superuser(username, email=email, password=password, **extra_fields)
