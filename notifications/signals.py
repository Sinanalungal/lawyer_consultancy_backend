from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notifications
from .tasks import send_notification_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from datetime import datetime

        
@receiver(post_save, sender=Notifications)
def notification_saved(sender, instance, created, **kwargs):
    if created:
        print(instance.pk, instance.id)
        print('Notification saved signal triggered for ID:', instance.id)  
        channel_layer = get_channel_layer()
        send_notification_task.apply_async(args=[instance.pk], eta=instance.notify_time)
        naive_datetime = datetime.now() 
        aware_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
        print(aware_datetime,'notification sending time')
        notification = Notifications.objects.filter(user=instance.user,notify_time__lte=aware_datetime, is_readed = False)
        print('this is the notifications',notification)
        print('this is the notification count',notification.count())
        async_to_sync(channel_layer.group_send)(
            f'notifications_count_{instance.user.pk}',
            {
                'type': 'send_notification_count',
                'notification_count':notification.count(),
            }
        )

        