
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
        user = self.request.user
        lookup = self.tenant_lookup or self.tenant_field

        if not user.is_authenticated:
            return queryset.none()

        # Contexto de Superusuario: Prioridad al Header X-Institution-ID para permitir cambio de tenant
        if user.is_superuser:
            header_inst_id = self.request.headers.get('X-Institution-ID')
            if header_inst_id and str(header_inst_id).isdigit():
                return queryset.filter(**{f"{lookup}_id": header_inst_id})
            
            # Si no hay header, pero tiene una institución asignada, la usamos como fallback
            user_inst = getattr(user, 'institution', None)
            if user_inst:
                return queryset.filter(**{lookup: user_inst})

            # Vista global si se solicita
            if self.request.query_params.get('global_view') == 'true':
                return queryset
            
            # Por defecto vacío si no hay contexto claro para superuser
            return queryset.none()

        # Contexto Institucional Estricto para usuarios normales
        user_inst = getattr(user, 'institution', None)
        if user_inst:
            return queryset.filter(**{lookup: user_inst})
        
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        header_inst_id = self.request.headers.get('X-Institution-ID')
        inst = None

        # Prioridad 1: Superuser con Header
        if user.is_superuser and header_inst_id and str(header_inst_id).isdigit():
            from users.models import Institution
            inst = Institution.objects.filter(id=header_inst_id).first()

        # Prioridad 2: Institución asignada al usuario
        if not inst:
            inst = getattr(user, 'institution', None)
        
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
