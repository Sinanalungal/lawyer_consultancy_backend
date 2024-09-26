from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notifications
from .tasks import send_notification_task

@receiver(post_save, sender=Notifications)
def notification_saved(sender, instance, created, **kwargs):
    if created:
        print(instance.pk, instance.id)
        print('Notification saved signal triggered for ID:', instance.id)  # Debug log
        send_notification_task.apply_async(args=[instance.pk], eta=instance.notify_time)
        print('Notify time set for task:', instance.notify_time)