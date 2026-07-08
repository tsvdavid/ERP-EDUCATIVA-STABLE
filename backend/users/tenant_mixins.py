
from django.db import models
from rest_framework.exceptions import ValidationError

class InstitutionFilterMixin:
    """
    Mixin para ViewSets que automatiza el filtrado multi-tenant por institución.
    Soporta contextos de Administrador Global y Local.
    """
    tenant_field = 'institution'    # Campo real en el modelo para perform_create
    tenant_lookup = None            # Lookup string para get_queryset (opcional)

    def get_queryset(self):
        queryset = super().get_queryset()
        lookup = self.tenant_lookup or self.tenant_field
        active_tenant = getattr(self.request, 'tenant', None)

        if not self.request.user.is_authenticated:
            return queryset.none()

        if not active_tenant:
            return queryset.none()

        return queryset.filter(**{f"{lookup}_id": active_tenant.id})

    def perform_create(self, serializer):
        inst = getattr(self.request, 'tenant', None)

        if not inst:
             raise ValidationError({
                 "detail": "Acción denegada: Se requiere un contexto de institución válido para crear registros."
             })
             
        save_kwargs = {}
        # Verificamos si el modelo tiene el campo de institución
        model = self.get_serializer().Meta.model
        if hasattr(model, self.tenant_field):
             save_kwargs[self.tenant_field] = inst
             
        serializer.save(**save_kwargs)
