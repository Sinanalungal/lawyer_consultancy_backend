from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer

User = get_user_model()

class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print('connected',event)
        await self.send({
            'type': 'websocket.accept',
        })
    
    async def websocket_recieve(self, event):
        print('recieved',event)

    async def websocket_disconnect(self, event):
        print('disconnected',event)