import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Debug output to verify authentication
        print("===== WEBSOCKET AUTH =====")
        print("USER:", self.scope.get("user"))
        print("AUTH:", getattr(self.scope.get("user"), "is_authenticated", False))
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Receive message from group
    async def notification_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': event['type'],
            'payload': event['payload']
        }))
