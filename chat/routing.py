from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path('user/chat/<int:id>',consumers.ChatConsumer.as_asgi()),
    path('lawyer/chat/<int:id>',consumers.ChatConsumer.as_asgi()),
]