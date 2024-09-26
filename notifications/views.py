from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics
from .models import Notifications
from .serializer import NotificationSerializer
from server.permissions import IsOwner


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        user = self.request.user
        return Notifications.objects.filter(user=user).order_by('-notify_time')
