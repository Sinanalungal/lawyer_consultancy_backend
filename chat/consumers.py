from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from api.models import CustomUser
from .models import Thread,ChatMessage
from datetime import datetime
import base64
from io import BytesIO
from django.core.files.base import ContentFile
import uuid
from decouple import config



User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        print('connected')
        # user_id = self.scope['url_route']['kwargs']['id']
        user = self.scope['user']
    
        if user.is_anonymous:
            # If the user is not authenticated, you can handle it here (e.g., close the connection)
            await self.close()
            return
        
        # Get the user ID from the user object
        user_id = user.id
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
        message_data = data.get('text',None)
        audio=data.get('audio',None)
        send_by_id = data.get('sent_by')
        send_to_id = data.get('send_to')
        thread = data.get('thread')
        content_type = data.get('content_type')
        # print(message_data,'this is message data')

        print(f"send_by_id:{send_by_id} and send_to_id:{send_to_id}")
      
        if not message_data and not audio:
            print('ERROR: No content data')
            return False
        sent_by_user = await self.get_user_objects(send_by_id)
        sent_to_user = await self.get_user_objects(send_to_id)
        thread_obj = await self.get_thread(thread)

        print(sent_by_user,'send_by_user')
        print(sent_to_user,'send_to_user')

        if not sent_by_user:
            print('Error: Send by user is incorrect')
        if not sent_to_user:
            print('Error: Send to user is incorrect')
        if not thread_obj:
            print('Error:: Thread id is incorrect')

        if audio:
            audio_base64_string_decoded=base64.b64decode(audio)
            audio = ContentFile(audio_base64_string_decoded,f'audio_file-{uuid.uuid4()}.mp3')

        obj = await self.create_chat_message(thread_obj,sent_by_user,message_data,content_type,audio)


        other_user_chat_room = f'user_chatroom_{send_to_id}'
        print(f'other_user_chat_room:{other_user_chat_room}')
        # user_id = self.scope['url_route']['kwargs']['id']

        current_time = datetime.now()
        print(current_time)
 
        if content_type == 'text':
            response = {
                'message': message_data,
                'audio':None,
                'video': None,
                'image': None,
                'send_by':send_by_id,
                'thread': thread,
                'content_type':content_type,
                'timestamp': str(current_time)
            }
        elif content_type == 'audio':
            print(obj.audio.url)
            response = {
                'message': None,
                'audio':f"{config('BACKEND_URL')}{obj.audio.url}",
                'video': None,
                'image': None,
                'send_by':send_by_id,
                'thread': thread,
                'content_type':content_type,
                'timestamp': str(current_time)
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

        # #making Thread as real time
        # await self.channel_layer.group_send(
        #     other_user_chat_room,
        #     {
        #         'type': 'thread_update',
        #         'text':''
        #     }
        # )


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

    async def add_thread(self, event):
        print('Add Thread')
        print(event,'this is the event')
        # await self.send(text_data=event['text'])
        await self.send(text_data=event['text'])


    @database_sync_to_async
    def get_user_objects(self, user_id):
        query_set = CustomUser.objects.filter(id=int(user_id))
        if query_set:
            return query_set.first()
        return None
    
    @database_sync_to_async
    def get_thread(self, thread):
        query_set = Thread.objects.filter(id=int(thread))
        if query_set:
            return query_set.first()
        return None
    
    @database_sync_to_async
    def create_chat_message(self, thread , user, msg,content_type,audio):
        if content_type =='text':
            obj = ChatMessage.objects.create(thread=thread,user=user,message=msg,content_type=content_type)
            print('text saved in database')
        elif content_type =='audio':
            obj = ChatMessage.objects.create(thread=thread,user=user,audio=audio,content_type=content_type)
            print('audio saved in database')
        return obj