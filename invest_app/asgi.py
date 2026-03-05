"""
ASGI config for invest_app.
Supports both HTTP (Django) and WebSocket (Django Channels) connections.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "invest_app.settings.local")

django_asgi_app = get_asgi_application()

import realtime.routing  # noqa: E402 — imported after Django setup

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(realtime.routing.websocket_urlpatterns))
        ),
    }
)
