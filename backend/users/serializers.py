from rest_framework import serializers
from .models import Institution, User

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'second_name', 'last_name', 'second_surname', 'cedula', 'photo', 'role', 'institution', 'phone', 'secondary_phone', 'address', 'birth_date', 'gender', 'notes', 'children', 'representative_name')
        read_only_fields = ('id',)
        extra_kwargs = {
            'password': {'write_only': True},
            'photo': {'required': False}
        }
    
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
        fields = ('id', 'username', 'password', 'email', 'first_name', 'second_name', 'last_name', 'second_surname', 'cedula', 'photo', 'role', 'institution', 'phone', 'secondary_phone', 'address', 'birth_date', 'gender', 'notes', 'representative_name')
    
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
