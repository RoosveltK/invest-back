"""WebSocket URL routing for realtime app."""
from django.urls import path

from realtime.consumers import ProjectConsumer

websocket_urlpatterns = [
    path("ws/projects/<int:project_id>/", ProjectConsumer.as_asgi()),
]
