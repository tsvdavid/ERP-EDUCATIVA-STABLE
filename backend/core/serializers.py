from rest_framework import serializers

class TenantSerializerMixin(metaclass=serializers.SerializerMetaclass):
    """
    Mixin para blindar serializadores en entornos multi-tenant.
    Valida automáticamente que la institución de los datos coincida con la del usuario.
    """
    def validate(self, data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return super().validate(data)

        # Si el usuario es superusuario, puede asignar cualquier institución (para gestión global)
        if request.user.is_superuser:
             return super().validate(data)

        # Para usuarios normales (Rectores, etc.), forzar su propia institución
        user_inst = getattr(request.user, 'institution', None)
        
        # 1. Si intentan enviar una institución diferente, rechazar
        if 'institution' in data:
            target_inst = data['institution']
            if user_inst and target_inst != user_inst:
                raise serializers.ValidationError({
                    "institution": "Violación de seguridad: No puedes crear/editar registros para otra institución."
                })
        
        # 2. Si no envían institución pero el modelo la requiere, asignarla automáticamente
        # Esto previene errores donde se olvida enviar el campo desde el frontend
        if user_inst and hasattr(self.Meta.model, 'institution'):
            if 'institution' not in data:
                data['institution'] = user_inst

        return super().validate(data)
