from celery import shared_task
from .models import Notifications
from schedule.models import BookedAppointment,PaymentDetails
from wallet.models import WalletTransactions
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from decimal import Decimal
import logging
from django.db import transaction
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)

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
        try:
            naive_datetime = datetime.now() 
            aware_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
            print(aware_datetime,'notification sending time')
            print(notification.user)
            unread_notification = Notifications.objects.filter(user=notification.user,notify_time__lte=aware_datetime, is_readed = False)
            print(unread_notification,'these are teh notifications that is not readed')
            print('this is the notifications',unread_notification)
            print('this is the notification count',unread_notification.count())
            async_to_sync(channel_layer.group_send)(
                f'notifications_count_{notification.user.pk}',
                {
                    'type': 'send_notification_count',
                    'notification_count':unread_notification.count(),
                }
            )
        except :
            print('error in sending notification count')


        print(f"Sent notification: {notification.title} to {notification.user.username}")
        return notification_data
    except Notifications.DoesNotExist:
        print(f"Notification with ID {notification_id} does not exist.")
    except Exception as e:
        print(f"Error in send_notification_task: {str(e)}") 


@shared_task(bind=True)
def send_money_to_the_lawyer_wallet(self, lawyer_id, payment_details_id, booked_session_id):
    print(booked_session_id, 'this is the booked session id')
    try:
        with transaction.atomic():
            booked_session = BookedAppointment.objects.get(id=booked_session_id)
            payment_details = PaymentDetails.objects.get(id=payment_details_id)

            latest_transaction = WalletTransactions.objects.filter(
                user_id=lawyer_id
            ).order_by('-created_at').first()

            latest_wallet_balance = latest_transaction.wallet_balance if latest_transaction else Decimal(0)
            
            # Calculate price for the lawyer (90% of the session price)
            price_for_lawyer = Decimal(booked_session.scheduling.price) * Decimal(0.9)
            updated_wallet_balance = latest_wallet_balance + price_for_lawyer

            # Create wallet transaction for the lawyer
            WalletTransactions.objects.create(
                user_id=lawyer_id,
                payment_details=payment_details,
                wallet_balance=updated_wallet_balance,
                amount=price_for_lawyer,
                transaction_type='credit'
            )

            # Mark the session as completed
            booked_session.is_completed = True
            booked_session.save()

            print(f"Money added to the lawyer's account")
            # return wallet_obj

    except BookedAppointment.DoesNotExist:
        logger.error(f"BookedAppointment with ID {booked_session_id} does not exist.")
    except PaymentDetails.DoesNotExist:
        logger.error(f"PaymentDetails with ID {payment_details_id} does not exist.")
    except Exception as e:
        logger.error(f"Error in send_money_to_the_lawyer_wallet task: {str(e)}")