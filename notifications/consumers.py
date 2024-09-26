import json
from channels.generic.websocket import AsyncWebsocketConsumer
from api.models import CustomUser
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user_id = self.scope['url_route']['kwargs']['id']
        self.user = await sync_to_async(get_object_or_404)(CustomUser, id=user_id)
        print(f"User connected: {self.user.username} with ID: {self.user.pk}")

        self.group_name = f'notifications_{self.user.pk}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        print(f"User added to group: {self.group_name}")

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        notification = event['notification']
        print('getting into the consumer send notification')
        print(event['notification'])
        try:
            await self.send(text_data=json.dumps({'notification': notification}))
        except Exception as e:
            print(f"Error sending notification: {str(e)}")

