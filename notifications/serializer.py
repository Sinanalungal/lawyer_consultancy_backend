from .models import Notifications 
from rest_framework import serializers

class NotificationSerializer(serializers.ModelSerializer):
    """serializer for notifications"""
    class Meta:
        model = Notifications
        fields= ['id','title','description','notify_time','is_readed']