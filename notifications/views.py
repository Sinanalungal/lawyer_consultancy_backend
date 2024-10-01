from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics
from .models import Notifications
from .serializer import NotificationSerializer
from server.permissions import IsOwner
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        user = self.request.user
        # print(make_aware(timezone.now()),'this is the time now')
        naive_datetime = datetime.now() 
        aware_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
        print(aware_datetime,'this is the local time now')
        whole_notifications_data = Notifications.objects.filter(
            user=user,
            notify_time__lte=aware_datetime
        ).order_by('-notify_time')

        channel_layer = get_channel_layer()
        not_readed_notifications = whole_notifications_data.filter(is_readed=False)

        not_readed_notifications.update(is_readed=True)  
        async_to_sync(channel_layer.group_send)(
            f'notifications_count_{user.pk}',
            {
                'type': 'send_notification_count',
                'notification_count':0,
            }
        )

        return whole_notifications_data
    
class NotificationCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        naive_datetime = datetime.now() 
        aware_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
        unread_notifications_count = Notifications.objects.filter(
            user=user,
            is_readed=False,
            notify_time__lte=aware_datetime
        ).count()
        
        return Response({"unread_count": unread_notifications_count if unread_notifications_count else 0})
    