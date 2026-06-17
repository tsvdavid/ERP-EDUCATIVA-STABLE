import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from communication.middleware import JwtAuthMiddleware
import communication.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": JwtAuthMiddleware(
        URLRouter(
            communication.routing.websocket_urlpatterns
        )
    ),
})
