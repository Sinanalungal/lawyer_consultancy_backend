from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from api.models import CustomUser


User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        print('connected')
        user_id = self.scope['url_route']['kwargs']['id']
        # print('Connected to room:', user_id)
        chat_room = f'user_chatroom_{user_id}'
        print(chat_room)
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        await self.accept()
        # print(self.scope)
        
    
    async def receive(self, text_data):
        print('received', text_data)
        data = json.loads(text_data)
        print(data)
        message_data = data.get('text')
        send_by_id = data.get('sent_by')
        send_to_id = data.get('send_to')

        print(f"send_by_id:{send_by_id} and send_to_id:{send_to_id}")
      
        if not message_data:
            print('ERROR: No message data')
            return False
        
        sent_by_user = await self.get_user_objects(send_by_id)
        sent_to_user = await self.get_user_objects(send_to_id)
        print(sent_by_user)
        print(sent_to_user)

        if not sent_by_user:
            print('Error: Send by user is incorrect')
        if not sent_to_user:
            print('Error: Send to user is incorrect')


        other_user_chat_room = f'user_chatroom_{send_to_id}'
        print(f'other_user_chat_room:{other_user_chat_room}')
        # user_id = self.scope['url_route']['kwargs']['id']

        response = {
            'message': message_data,
            'send_by':send_by_id
        }

        print(message_data,'message_data')
        await self.channel_layer.group_send(
            other_user_chat_room,
            {
                'type': 'chat_message',
            #    'send_by': user_id,
                'text': json.dumps(response),
            }
        )
        await self.channel_layer.group_send(
            self.chat_room,
            {
                'type': 'chat_message',
            #    'send_by': user_id,
                'text': json.dumps(response),
            }
        )
        #Echo the received message
        # await self.send(text_data=json.dumps({
        #     'send_by': user_id,
        #     'text': message_data,
        # }))
    

    async def disconnect(self, close_code):
        print('disconnected')


    async def chat_message(self, event):
        print('chat message')
        print(event,'this is the event')
        # await self.send(text_data=event['text'])
        await self.send(text_data=event['text'])


    @database_sync_to_async
    def get_user_objects(self, user_id):
        query_set = CustomUser.objects.filter(id=int(user_id))
        if query_set:
            return query_set.first()
        return None