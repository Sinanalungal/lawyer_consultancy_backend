# from django.db import models
# from api.models import CustomUser
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# # from .models import Message
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# import json

# class Message(models.Model):
#     sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     content = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)


# @receiver(post_save, sender=Message)
# def send_message_notification(sender, instance, **kwargs):
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         "chat_group",
#         {
#             "type": "chat.message",
#             "message": json.dumps({
#                 "sender": instance.sender.username,
#                 "content": instance.content,
#                 "timestamp": instance.timestamp.strftime("%Y-%m-%d %H:%M:%S")
#             })
#         }
#     )