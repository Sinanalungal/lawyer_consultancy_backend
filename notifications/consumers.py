import json
from channels.generic.websocket import AsyncWebsocketConsumer
from api.models import CustomUser
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer for handling real-time notifications via WebSocket.
    """

    async def connect(self):
        """
        Connects the user to the WebSocket and adds them to the notification group.
        """
        user_id = self.scope['url_route']['kwargs']['id']
        self.user = await sync_to_async(get_object_or_404)(CustomUser, id=user_id)
        print(f"User connected: {self.user.username} with ID: {self.user.pk}")

        self.group_name = f'notifications_{self.user.pk}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        print(f"User added to group: {self.group_name}")

        await self.accept()

    async def disconnect(self, close_code):
        """
        Disconnects the user from the WebSocket and removes them from the group.
        """
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        """
        Sends a notification message to the WebSocket.

        Args:
            event (dict): Contains the notification data to be sent.
        """
        notification = event['notification']
        print('getting into the consumer send notification')
        print(event['notification'])
        try:
            await self.send(text_data=json.dumps({'notification': notification}))
        except Exception as e:
            print(f"Error sending notification: {str(e)}")


class NotificationCountConsumer(AsyncWebsocketConsumer):
    """
    Consumer for handling real-time notification counts via WebSocket.
    """

    async def connect(self):
        """
        Connects the user to the WebSocket and adds them to the notification count group.
        """
        user_id = self.scope['url_route']['kwargs']['id']
        self.user = await sync_to_async(get_object_or_404)(CustomUser, id=user_id)
        print(f"User connected: {self.user.username} with ID: {self.user.pk}")

        self.group_name = f'notifications_count_{self.user.pk}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        print(f"User added to group: {self.group_name}")

        await self.accept()

    async def disconnect(self, close_code):
        """
        Disconnects the user from the WebSocket and removes them from the group.
        """
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # This method handles 'send_notification_count' messages
    async def send_notification_count(self, event):
        """
        Sends the notification count to the WebSocket.

        Args:
            event (dict): Contains the notification count to be sent.
        """
        notification_count = event['notification_count']
        print(event, 'this is the event in the send_notification')
        print(event['notification_count'])

        try:
            # Send the notification count to WebSocket
            await self.send(text_data=json.dumps({'notification_count': notification_count}))
        except Exception as e:
            print(f"Error sending notification count: {str(e)}")
