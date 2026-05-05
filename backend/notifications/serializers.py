from rest_framework import serializers
from .models import EmailConfig, EmailTemplate, EmailLog

class EmailConfigSerializer(serializers.ModelSerializer):
    smtp_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = EmailConfig
        fields = [
            'id', 'institution', 'smtp_host', 'smtp_port', 'smtp_user', 
            'smtp_password', 'use_tls', 'use_ssl', 'sender_name', 
            'sender_email', 'is_active'
        ]
        read_only_fields = ['institution']

    def validate(self, data):
        """
        Regla obligatoria:
        Si use_ssl=true entonces use_tls=false
        Si use_tls=true entonces use_ssl=false
        """
        use_tls = data.get('use_tls')
        use_ssl = data.get('use_ssl')

        if use_tls and use_ssl:
            raise serializers.ValidationError({
                "non_field_errors": ["No se pueden habilitar SSL y TLS simultáneamente. Elija uno."]
            })

        # Validación básica de email si no es EmailField en el modelo
        sender_email = data.get('sender_email')
        if sender_email and '@' not in sender_email:
            raise serializers.ValidationError({
                "sender_email": ["Ingrese un correo electrónico válido."]
            })

        return data

    def create(self, validated_data):
        password = validated_data.pop('smtp_password', None)
        instance = super().create(validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop('smtp_password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ['id', 'institution', 'code', 'subject', 'html_body', 'is_active']
        read_only_fields = ['institution']

class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = [
            'id', 'institution', 'recipient', 'subject', 'status', 
            'error_message', 'sent_at', 'created_at', 'reference_id', 
            'module_origin'
        ]
        read_only_fields = ['institution', 'created_at', 'sent_at']
