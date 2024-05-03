# from twilio.rest import Client
# from django.conf import settings

# def send_sms(to, body):
#     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#     message = client.messages.create(
#         body=body,
#         from_=settings.TWILIO_PHONE_NUMBER,
#         to=to
#     )
#     return message

from django.conf import settings
from twilio.rest import Client
import random

def generate_otp():
    return str(random.randint(100000, 999999))  

# def send_otp(to, otp):
#     try:
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#         message_body = f'Your OTP is: {otp}'
#         message = client.messages.create(
#             body=message_body,
#             from_=settings.TWILIO_PHONE_NUMBER,
#             to=to
#         )
#         return True, 'OTP sent successfully'
#     except Exception as e:
#         return False, str(e)



