from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification, Message

@receiver(post_save, sender=Notification)
def send_notification_socket(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        group_name = f"user_{instance.user.id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notification_message",
                "payload": {
                    "type": "NOTIFICATION",
                    "id": instance.id,
                    "title": instance.title,
                    "message": instance.message,
                    "priority": instance.priority
                }
            }
        )

@receiver(post_save, sender=Message)
def send_message_socket(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        group_name = f"user_{instance.recipient.id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notification_message",
                "payload": {
                    "type": "NEW_MESSAGE",
                    "id": instance.id,
                    "sender": instance.sender.username,
                    "subject": instance.subject
                }
            }
        )
