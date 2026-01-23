from rest_framework import serializers
from .models import Message, Notification, Notice, Holiday
from users.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    recipient_username = serializers.CharField(write_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('sender', 'recipient', 'created_at', 'is_read')

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        username = validated_data.pop('recipient_username')
        try:
            recipient = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({"recipient_username": "Usuario no encontrado con ese login."})

        validated_data['recipient'] = recipient
        # Auto-assign sender from context
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('created_at', 'is_read')

class NoticeSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = Notice
        fields = '__all__'
        read_only_fields = ('author', 'created_at')



class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'
        read_only_fields = ('id',)
