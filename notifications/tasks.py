from celery import shared_task
from .models import Notifications
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

@shared_task(bind=True)
def test_task(self):
    print('This is the test task')
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_2',
        {
            'type': 'send_notification',
            'notification': json.dumps('Hi'),
        }
    )
    return 'working'
    
@shared_task(bind=True)
def send_notification_task(self, notification_id):
    print(notification_id, 'this is the notification id')
    try:
        notification = Notifications.objects.get(id=notification_id)

        notification_data = {
            'title': notification.title,
            'description': notification.description,
            'user_id': notification.user.pk,
            'time': notification.notify_time.isoformat(),
        }
        print(notification.user.pk, 'this is the user pk')
        print(notification_data, 'this is the notification data')

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{notification.user.pk}',
            {
                'type': 'send_notification',
                'notification': json.dumps(notification_data),
            }
        )

        print(f"Sent notification: {notification.title} to {notification.user.username}")
        return notification_data
    except Notifications.DoesNotExist:
        print(f"Notification with ID {notification_id} does not exist.")
    except Exception as e:
        print(f"Error in send_notification_task: {str(e)}")  # Log any other errors
