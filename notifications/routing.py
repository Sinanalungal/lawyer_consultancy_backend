from django.urls import path
from .consumers import NotificationConsumer,NotificationCountConsumer

websocket_urlpatterns = [
    path('notifications/<int:id>/', NotificationConsumer.as_asgi()),
    path('notification-count/<int:id>/', NotificationCountConsumer.as_asgi()),
]
