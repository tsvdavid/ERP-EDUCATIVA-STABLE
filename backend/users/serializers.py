from rest_framework import serializers
from .models import Institution, User

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = [
            'id', 'name', 'address', 'phone', 'email', 'website', 'logo',
            'ruc', 'establishment_code', 'emission_point', 'obligado_contabilidad',
            'sri_environment', 'electronic_signature', 'signature_password',
            'special_taxpayer_number',
            'sri_url_reception_test', 'sri_url_authorization_test',
            'sri_url_reception_prod', 'sri_url_authorization_prod',
            'setup_status', 'setup_error', 'setup_completed_at', 'wizard_completed',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['setup_status', 'setup_error', 'setup_completed_at', 'wizard_completed']

    def validate(self, data):
        # HARDENING: In a PATCH request, we only validate fields present in the data.
        # However, for creation or full update, we check all required fields.
        is_patch = self.partial if hasattr(self, 'partial') else False
        
        required_fields = ['name', 'ruc', 'address', 'phone', 'email', 'establishment_code', 'emission_point']
        errors = {}
        
        for field in required_fields:
            # If it's a PATCH and the field is not in data, we don't validate it (it stays as is in DB)
            if is_patch and field not in data:
                continue
                
            if not data.get(field):
                errors[field] = f"El campo {field} es obligatorio."
                
        if errors:
            raise serializers.ValidationError(errors)
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'second_name', 'last_name', 'second_surname', 'cedula', 'photo', 'role', 'is_staff', 'is_superuser', 'institution', 'phone', 'secondary_phone', 'address', 'birth_date', 'gender', 'notes', 'nationality', 'civil_status', 'titles', 'teaching_category', 'children')
        read_only_fields = ('id',)
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        # Detailed representation of children for parents
        if instance.children.exists():
            response['children'] = UserSerializer(instance.children.all(), many=True, context=self.context).data
        return response

    def validate_cedula(self, value):
        if not value:
            return None
        return value

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'second_name', 'last_name', 'second_surname', 'cedula', 'photo', 'role', 'institution', 'phone', 'secondary_phone', 'address', 'birth_date', 'gender', 'notes', 'nationality', 'civil_status', 'titles', 'teaching_category')
        read_only_fields = ('institution',)

    def __init__(self, *args, **kwargs):
        super(UserCreateSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            tenant = request.tenant
            if tenant:
                self.fields['institution'].queryset = Institution.objects.filter(id=tenant.id)

    
    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.role == 'RECTOR':
            if data.get('role') == 'ADMIN':
                raise serializers.ValidationError({"role": "Los Rectores no pueden crear usuarios Administradores."})
        return data

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
             raise serializers.ValidationError("El nombre de usuario ya existe en el sistema. Por favor elija otro (ej: usuario.apellido).")
        return value

    def validate_cedula(self, value):
        if not value:
            return None
        return value

    def create(self, validated_data):
        try:
            password = validated_data.pop('password')
            user = User(**validated_data)
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
