from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Thread
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import ThreadForSiganlsSerializer 
import json

@receiver(post_save, sender=Thread)
def chat_message_handler(sender, instance, **kwargs):
    print('Entering signal handler')
    channel_layer = get_channel_layer()
    print(channel_layer,'this is the channel layer')

    print(instance)
    
    # Determine the chat room to send the message to
    chat_room = f'user_chatroom_{instance.second_person.id}'  # Adjust this as needed
    print(f'Chat room: {chat_room}')
    
    # Serialize the Thread instance
    try:
        serializer = ThreadForSiganlsSerializer(instance, context={
            'request_user': instance.second_person
        })
        message_data = serializer.data
        print(message_data,'this is the signal serialized data')
        # Send the serialized data to the WebSocket consumer
        async_to_sync(channel_layer.group_send)(
            chat_room,
            {
                'type': 'add_thread',
                'text': json.dumps(message_data)
            }
        )
        print('Message sent to chat room')
    except Exception as e:
        print(f'Error sending message: {e}')
