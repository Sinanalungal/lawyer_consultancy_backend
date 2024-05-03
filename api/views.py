# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from .serializers import UserRegistrationSerializer ,OtpSerializer
# from django_redis import get_redis_connection
# from .sms_utils import  generate_otp
# import json
# from django.conf import settings
# from twilio.rest import Client
# from rest_framework.decorators import permission_classes
# from .permissions import IsAdmin, IsLawyer, IsUser
# from rest_framework.permissions import IsAuthenticated
# from django.utils import timezone
# from datetime import timedelta,datetime
# import pytz








# class MessageHandler:
#     """Handles sending OTP messages."""
#     phone_number = None
#     otp = None
    
#     def __init__(self, phone_number, otp) -> None:
#         self.phone_number = phone_number
#         self.otp = otp
    
#     def send_otp_via_message(self):     
#         """Send OTP via SMS."""
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#         message = client.messages.create(body=f'Your One Time OTP For Zephyr Registrations is: {self.otp}. Do not share this OTP with anyone',
#                                         from_=f'{settings.TWILIO_PHONE_NUMBER}',
#                                         to=f'{settings.COUNTRY_CODE}{self.phone_number}')




# class UserRegistrationAPIView(APIView):
#     def post(self, request, format=None):
#         print('start working')
#         serializer = UserRegistrationSerializer(data=request.data)
#         if serializer.is_valid():
#             print('inside the valid')
#             role = serializer.validated_data.get('role')

#             print(role == 'user')
#             if role == 'user':
#                 print(serializer.validated_data)
#                 redis_conn = get_redis_connection("default")

#                 registration_key = f"{serializer.validated_data['email']}"
#                 data_json = redis_conn.get(serializer.validated_data['email'])
#                 data_to_store = json.dumps(serializer.validated_data)
#                 redis_conn.setex(registration_key, 3600, data_to_store.encode('utf-8'))  


#                 print(data_json,'this')

#                 # if data_json:
#                 #     data_dict = json.loads(data_json.decode('utf-8'))
#                 #     print(data_dict)
#                 # else:
#                 #     print("Data not found in Redis")


#                 otp_code = generate_otp()
#                 otp_key = f"otp_{serializer.validated_data['email']}"
#                 redis_conn.setex(otp_key, 60, str(otp_code))

#                 new_time = timezone.now() + timedelta(seconds=31)
#                 new_time_timestamp = new_time.timestamp() 


#                 print(f"New Time: {new_time}")

#                 expiration_time = f"expiration_{serializer.validated_data['email']}"
#                 redis_conn.setex(expiration_time, 3600, new_time_timestamp)

#                 obj=MessageHandler(serializer.validated_data['phone_number'], otp_code)
#                 obj.send_otp_via_message()


#                 return Response({"data": {'email': serializer.validated_data['email'], 'phone_number': serializer.validated_data['phone_number']}, "message": "OTP sent for verification"}, status=status.HTTP_200_OK)
#             else:
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# class OtpVerificationView(APIView):
#     def post(self, request, *args, **kwargs):
#         print(request.data)
#         email = request.data['email']
#         print(email)
#         print(request.data['otp'])
        
#         serializer = UserRegistrationSerializer(data={'otp':request.data['otp']})
#         # if serializer.is_valid():
#         print('inside the valid')
#         redis_conn = get_redis_connection("default")
#         time=float(redis_conn.get(f"expiration_{email}").decode('utf-8'))
#         valid_time=datetime.utcfromtimestamp(time)
#         # valid_time_aware = timezone.make_aware(valid_time, timezone.get_current_timezone())
#         # new_time = current_time + timedelta(seconds=30)
        
#         print(valid_time.time(),'full')
#         print((timezone.now()).time(),'now')
#         if valid_time >= timezone.now():
#             print('entered it to')
#             print(redis_conn.get(f"expiration_{email}"))
#             redis_otp = redis_conn.get(f"otp_{email}")
#             print(redis_otp,'otp')
#             if redis_otp:
#                 otp_redis = json.loads(redis_otp.decode('utf-8'))
#                 if otp_redis == serializer.validated_data('otp'):
#                     data_json = redis_conn.get(serializer.validated_data['email'])
#                     if data_json:
#                         try:
#                             data_dict = json.loads(data_json.decode('utf-8'))
#                             print(data_dict)
#                             data_dict.pop('role')
#                             serializer = UserRegistrationSerializer(data=data_dict)
#                             if serializer.is_valid():
#                                 validated_data = serializer.validated_data
#                                 validated_data['is_verified'] = True
#                                 instance = serializer.save()
#                                 print('everythig successfully registered')
#                             return Response({'message':'Registration Successfull'}, status=status.HTTP_201_CREATED)
                        
#                         except Exception as e:
#                             print(e)
#                     else:
#                         print("Data not found in Redis") 
#                 else:
#                     print('not correct otp')
#             else:
#                 print('no otp in redis')
#         else:
#             print('register once again')
#         # else:
#         #     print('enter a valid otp')
        





# # from django.shortcuts import render
# # # from .sms_utils import send_otp, generate_otp

# # def send_otp_message(request):
# #     if request.method == 'POST':
# #         to_number = request.POST.get('to_number')  # Get recipient's number
        
# #         # Generate OTP
# #         otp = generate_otp()
        
# #         # Send OTP via Twilio
# #         response = send_otp(to_number, otp)
# #         # Handle response as needed

# #         return render(request, 'send_otp.html', {'response': response})
# #     return render(request, 'send_otp.html')



from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer, OtpSerializer
from django_redis import get_redis_connection
from .sms_utils import generate_otp
import json
from django.conf import settings
from twilio.rest import Client
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class MessageHandler:
    """Handles sending OTP messages."""
    phone_number = None
    otp = None
    
    def __init__(self, phone_number, otp) -> None:
        self.phone_number = phone_number
        self.otp = otp
    
    def send_otp_via_message(self):     
        """Send OTP via SMS."""
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(body=f'Your One Time OTP For Connect Registrations is: {self.otp}. Do not share this OTP with anyone',
                                        from_=f'{settings.TWILIO_PHONE_NUMBER}',
                                        to=f'{settings.COUNTRY_CODE}{self.phone_number}')

class UserRegistrationAPIView(APIView):
    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.validated_data.get('role')
            if role == 'user':
                redis_conn = get_redis_connection("default")
                email = serializer.validated_data['email']

                # Store user data in Redis
                data_to_store = json.dumps(serializer.validated_data)
                redis_conn.setex(email, 3600, data_to_store.encode('utf-8'))

                # Generate OTP and store it in Redis
                otp_code = generate_otp()
                otp_key = f"otp_{email}"
                redis_conn.setex(otp_key, 60, str(otp_code))

                # Set expiration time for OTP verification
                expiration_key = f"expiration_{email}"
                expiration_time = timezone.now() + timedelta(seconds=31)
                expiration_seconds = int(expiration_time.timestamp())
                redis_conn.setex(expiration_key, 3600, expiration_seconds)

                # Send OTP via message
                obj = MessageHandler(serializer.validated_data['phone_number'], otp_code)
                obj.send_otp_via_message()


                return Response({"data": {'email': email, 'phone_number': serializer.validated_data['phone_number']},'timer':(expiration_time), "message": "OTP send to your phone number"}, status=status.HTTP_200_OK)
            else:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OtpVerificationView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        otp = request.data.get('otp')

        redis_conn = get_redis_connection("default")
        stored_otp = redis_conn.get(f"otp_{email}")
        if stored_otp and stored_otp.decode('utf-8') == otp:
            expiration_key = f"expiration_{email}"
            expiration_time = redis_conn.get(expiration_key)
            if expiration_time and float(expiration_time.decode('utf-8')) >= timezone.now().timestamp():
                
                # Your logic for verified OTP and within expiration time
                data_json = redis_conn.get(email)
                if data_json:
                    try:
                        data_dict = json.loads(data_json.decode('utf-8'))
                        print(data_dict)
                        role = data_dict.pop('role') 
                        serializer = UserRegistrationSerializer(data=data_dict)
                        if serializer.is_valid():
                            validated_data = serializer.validated_data
                            
                            instance = serializer.save()
                            # instance.is_verified = True
                            # instance.save()
                            print('Everything successfully registered')
                            return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
                    except Exception as e:
                        print(e)
                        return Response({"message": "Error processing data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return Response({"message": "Data not found in Redis"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"message": "OTP expired or invalid"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        

class ResendOtp(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        redis_conn = get_redis_connection("default")
        data_json = redis_conn.get(email)
        if data_json:
            try:
                data_dict = json.loads(data_json.decode('utf-8'))
                otp_code = generate_otp()
                otp_key = f"otp_{email}"
                redis_conn.setex(otp_key, 60, str(otp_code))

                # Set expiration time for OTP verification
                expiration_key = f"expiration_{email}"
                expiration_time = timezone.now() + timedelta(seconds=31)
                expiration_seconds = int(expiration_time.timestamp())
                redis_conn.setex(expiration_key, 3600, expiration_seconds)
                print(phone_number)
                obj = MessageHandler(phone_number, otp_code)
                obj.send_otp_via_message()

                
                return Response({"message": "OTP Resended Successfully",'timer':expiration_time}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({"message": "Please Register once again "}, status=status.HTTP_408_REQUEST_TIMEOUT)
        else:
            return Response({"message": "Please Register once again "}, status=status.HTTP_408_REQUEST_TIMEOUT)
        


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer to include additional user information in the token.
    """

    @classmethod
    def get_token(cls, user):
        print(user)
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['phone_number'] = user.phone_number
        token['email'] = user.email
        token['role'] = user.role
        token['is_verified'] = user.is_verified
        print(user.role)
        print(token)
        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
