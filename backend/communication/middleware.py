from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


class JwtAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):

        # Deferred imports to avoid AppRegistryNotReady
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model

        scope["user"] = AnonymousUser()

        try:
            query_string = scope.get("query_string", b"").decode()

            token = None

            for item in query_string.split("&"):
                key, value = item.split("=", 1)
                if key == "token":
                    token = value
                    break

            if token:
                access_token = AccessToken(token)
                user_id = access_token["user_id"]
                User = get_user_model()
                user = await self.get_user(User, user_id)
                if user:
                    scope["user"] = user
        except Exception as e:
            print(f"WebSocket JWT authentication failed: {e}")

        return await super().__call__(scope, receive, send)

    @staticmethod
    async def get_user(User, user_id):
        from asgiref.sync import sync_to_async
        try:
            return await sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            return None

