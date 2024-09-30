from django.urls import path
from .consumers import CallConsumer

websocket_urlpatterns = [
    path("ws/call/", CallConsumer.as_asgi()),
]
