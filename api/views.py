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
from django.shortcuts import get_object_or_404
from .models import CustomUser, PasswordResetToken
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from server.constants import url
from .utils import get_id_token_with_code_method_1, get_id_token_with_code_method_2
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
import jwt


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
        message = client.messages.create(
            body=f'Your One Time OTP For Connect Registrations is: {self.otp}. Do not share this OTP with anyone',
            from_=f'{settings.TWILIO_PHONE_NUMBER}',
            to=f'{settings.COUNTRY_CODE}{self.phone_number}'
        )


class UserRegistrationAPIView(APIView):
    """Handles user registration."""

    def post(self, request, format=None):
        """Handle POST request for user registration."""
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

                return Response({"data": {'email': email, 'phone_number': serializer.validated_data['phone_number']}, 'timer': expiration_time, "message": "OTP send to your phone number"}, status=status.HTTP_200_OK)
            else:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OtpVerificationView(APIView):
    """Handles OTP verification."""

    def post(self, request, *args, **kwargs):
        """Handle POST request for OTP verification."""
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
                        role = data_dict.pop('role')
                        serializer = UserRegistrationSerializer(data=data_dict)
                        if serializer.is_valid():
                            validated_data = serializer.validated_data
                            instance = serializer.save()
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
    """Handles resending OTP."""

    def post(self, request, *args, **kwargs):
        """Handle POST request for resending OTP."""
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

                obj = MessageHandler(phone_number, otp_code)
                obj.send_otp_via_message()

                return Response({"message": "OTP Resended Successfully", 'timer': expiration_time}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({"message": "Please Register once again "}, status=status.HTTP_408_REQUEST_TIMEOUT)
        else:
            return Response({"message": "Please Register once again "}, status=status.HTTP_408_REQUEST_TIMEOUT)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer to include additional user information in the token."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['phone_number'] = user.phone_number
        token['email'] = user.email
        token['role'] = user.role
        token['is_verified'] = user.is_verified

        if user.phone_number == '':
            token['registering'] = True

        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class ForgetPasswordView(APIView):
    """Handles forget password functionality."""

    def post(self, request, *args, **kwargs):
        """Handle POST request for forget password."""
        email = request.data.get('email')
        user = get_object_or_404(CustomUser, email=email)
        if user:
            token = get_random_string(length=20)
            PasswordResetToken.objects.update_or_create(user=user, defaults={'token': token})
            reset_link = f'{url}/reset-password/{token}/'
            send_mail(
                'Reset Your Password [only valid for 24 hours]:',
                f'Click the link to reset your password: {reset_link}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return Response({"message": "Forget password link sended into your Email"}, status=status.HTTP_200_OK)
        return Response({"message": "Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """Handles password reset functionality."""

    def post(self, request, *args, **kwargs):
        """Handle POST request for resetting password."""
        try:
            token = request.data.get('token')
            new_password = request.data.get('password')

            token_obj = get_object_or_404(PasswordResetToken, token=token)

            current_time = timezone.now()
            time_difference = current_time - token_obj.created_at

            if time_difference.total_seconds() > 86400:
                return Response({"message": "Reset token has expired"}, status=status.HTTP_400_BAD_REQUEST)

            user = token_obj.user
            user.set_password(new_password)
            user.save()
            token_obj.delete()
            return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)

        except PasswordResetToken.DoesNotExist:
            return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginWithGoogleView(APIView):
    """Handles Google authentication."""

    def authenticate_or_create_user(self, email, name, password):
        status = 'existed'
        try:
            user = CustomUser.objects.get(email=email)
            if user.phone_number == '':
                status = 'new'
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(username=email, email=email, full_name=name)
            user.set_password(password[0:10])
            user.save()
            status = 'new'

        return {'user': user, 'status': status}

    def get_jwt_token(self, user):
        token = AccessToken.for_user(user)
        refresh = RefreshToken.for_user(user)
        additional_data = {
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'email': user.email,
            'role': user.role,
            'is_verified': user.is_verified,
        }
        token.payload.update(additional_data)
        refresh.payload.update(additional_data)

        return {'refresh': str(refresh), 'access': str(token)}

    def post(self, request, *args, **kwargs):
        """Handle POST request for Google authentication."""
        if 'code' in request.data.keys():
            code = request.data.get('code')
            id_token = get_id_token_with_code_method_2(code)
            user_email = id_token.get('email')
            user = self.authenticate_or_create_user(user_email, id_token.get('name'), id_token.get('at_hash'))
            token = self.get_jwt_token(user.get('user'))
            registering = False
            if user.get('status') == 'new':
                registering = True

            return Response({'access_token': token, 'username': user_email, 'registering': registering},
                            status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Something wrong with google authentication'},
                            status=status.HTTP_400_BAD_REQUEST)


class SaveDataRequestView(APIView):
    """Handles saving user data."""

    def post(self, request, *args, **kwargs):
        """Handle POST request for saving user data."""
        try:
            phone_number = request.data.get('phone_number')
            email = request.data.get('email')
            otp = request.data.get('otp')
            print(phone_number, email, otp)
            redis_conn = get_redis_connection("default")
            stored_otp = redis_conn.get(f"otp_{email}")
            if stored_otp and stored_otp.decode('utf-8') == otp:
                expiration_key = f"expiration_{email}"
                expiration_time = redis_conn.get(expiration_key)
                if expiration_time and float(expiration_time.decode('utf-8')) >= timezone.now().timestamp():
                    if 'password' in request.data.keys():
                        password = request.data.get('password')
                        user = get_object_or_404(CustomUser, email=email)
                        user.phone_number = phone_number
                        user.set_password(password)
                        user.save()
                    else:
                        user = get_object_or_404(CustomUser, email=email)
                        user.phone_number = phone_number
                        user.save()
                    return Response({'message': 'Data saved successfully'}, status=status.HTTP_200_OK)
                else:
                    return  Response({'message': 'time out'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'message': 'Otp is not Valid'}, status=status.HTTP_400_BAD_REQUEST)
        except: 
            return Response({'message': 'Something wrong'}, status=status.HTTP_400_BAD_REQUEST)


class OtpSendGoogleAuthView(APIView):
    """Handles resending OTP."""

    def post(self, request, *args, **kwargs):
        """Handle POST request for resending OTP."""
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        redis_conn = get_redis_connection("default")
        try:
            otp_code = generate_otp()
            otp_key = f"otp_{email}"
            redis_conn.setex(otp_key, 60, str(otp_code))

            # Set expiration time for OTP verification
            expiration_key = f"expiration_{email}"
            expiration_time = timezone.now() + timedelta(seconds=31)
            expiration_seconds = int(expiration_time.timestamp())
            redis_conn.setex(expiration_key, 3600, expiration_seconds)

            obj = MessageHandler(phone_number, otp_code)
            obj.send_otp_via_message()

            return Response({"message": "OTP Resended Successfully", 'timer': expiration_time}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message": "Please Register once again "}, status=status.HTTP_408_REQUEST_TIMEOUT)
       
# ---------------------------------------------------------------------------------------------------------#





# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from .serializers import UserRegistrationSerializer, OtpSerializer
# from django_redis import get_redis_connection
# from .sms_utils import generate_otp
# import json
# import requests
# from django.conf import settings
# from twilio.rest import Client
# from rest_framework.permissions import IsAuthenticated
# from django.utils import timezone
# from datetime import timedelta
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework_simplejwt.views import TokenObtainPairView
# from django.shortcuts import get_object_or_404
# from .models import CustomUser,PasswordResetToken
# from django.utils.crypto import get_random_string
# from django.core.mail import send_mail
# from server.constants import url
# from .utils import get_id_token_with_code_method_1,get_id_token_with_code_method_2
# from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
# import jwt

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
#         message = client.messages.create(body=f'Your One Time OTP For Connect Registrations is: {self.otp}. Do not share this OTP with anyone',
#                                         from_=f'{settings.TWILIO_PHONE_NUMBER}',
#                                         to=f'{settings.COUNTRY_CODE}{self.phone_number}')

# class UserRegistrationAPIView(APIView):
#     def post(self, request, format=None):
#         serializer = UserRegistrationSerializer(data=request.data)
#         if serializer.is_valid():
#             role = serializer.validated_data.get('role')
#             if role == 'user':
#                 redis_conn = get_redis_connection("default")
#                 email = serializer.validated_data['email']

#                 # Store user data in Redis
#                 data_to_store = json.dumps(serializer.validated_data)
#                 redis_conn.setex(email, 3600, data_to_store.encode('utf-8'))

#                 # Generate OTP and store it in Redis
#                 otp_code = generate_otp()
#                 otp_key = f"otp_{email}"
#                 redis_conn.setex(otp_key, 60, str(otp_code))

#                 # Set expiration time for OTP verification
#                 expiration_key = f"expiration_{email}"
#                 expiration_time = timezone.now() + timedelta(seconds=31)
#                 expiration_seconds = int(expiration_time.timestamp())
#                 redis_conn.setex(expiration_key, 3600, expiration_seconds)

#                 # Send OTP via message
#                 obj = MessageHandler(serializer.validated_data['phone_number'], otp_code)
#                 obj.send_otp_via_message()


#                 return Response({"data": {'email': email, 'phone_number': serializer.validated_data['phone_number']},'timer':(expiration_time), "message": "OTP send to your phone number"}, status=status.HTTP_200_OK)
#             else:
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class OtpVerificationView(APIView):
#     def post(self, request, *args, **kwargs):
#         email = request.data.get('email')
#         otp = request.data.get('otp')

#         redis_conn = get_redis_connection("default")
#         stored_otp = redis_conn.get(f"otp_{email}")
#         if stored_otp and stored_otp.decode('utf-8') == otp:
#             expiration_key = f"expiration_{email}"
#             expiration_time = redis_conn.get(expiration_key)
#             if expiration_time and float(expiration_time.decode('utf-8')) >= timezone.now().timestamp():
                
#                 # Your logic for verified OTP and within expiration time
#                 data_json = redis_conn.get(email)
#                 if data_json:
#                     try:
#                         data_dict = json.loads(data_json.decode('utf-8'))
#                         print(data_dict)
#                         role = data_dict.pop('role') 
#                         serializer = UserRegistrationSerializer(data=data_dict)
#                         if serializer.is_valid():
#                             validated_data = serializer.validated_data
                            
#                             instance = serializer.save()
#                             # instance.is_verified = True
#                             # instance.save()
#                             print('Everything successfully registered')
#                             return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
#                     except Exception as e:
#                         print(e)
#                         return Response({"message": "Error processing data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#                 else:
#                     return Response({"message": "Data not found in Redis"}, status=status.HTTP_404_NOT_FOUND)
#             else:
#                 return Response({"message": "OTP expired or invalid"}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        

# class ResendOtp(APIView):
#     def post(self, request, *args, **kwargs):
#         email = request.data.get('email')
#         phone_number = request.data.get('phone_number')
#         redis_conn = get_redis_connection("default")
#         data_json = redis_conn.get(email)
#         if data_json:
#             try:
#                 data_dict = json.loads(data_json.decode('utf-8'))
#                 otp_code = generate_otp()
#                 otp_key = f"otp_{email}"
#                 redis_conn.setex(otp_key, 60, str(otp_code))

#                 # Set expiration time for OTP verification
#                 expiration_key = f"expiration_{email}"
#                 expiration_time = timezone.now() + timedelta(seconds=31)
#                 expiration_seconds = int(expiration_time.timestamp())
#                 redis_conn.setex(expiration_key, 3600, expiration_seconds)
#                 print(phone_number)
#                 obj = MessageHandler(phone_number, otp_code)
#                 obj.send_otp_via_message()

                
#                 return Response({"message": "OTP Resended Successfully",'timer':expiration_time}, status=status.HTTP_200_OK)
#             except Exception as e:
#                 print(e)
#                 return Response({"message": "Please Register once again "}, status=status.HTTP_408_REQUEST_TIMEOUT)
#         else:
#             return Response({"message": "Please Register once again "}, status=status.HTTP_408_REQUEST_TIMEOUT)
        


# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     """
#     Custom token serializer to include additional user information in the token.
#     """

#     @classmethod
#     def get_token(cls, user):
#         print(user)
#         token = super().get_token(user)
#         token['full_name'] = user.full_name
#         token['phone_number'] = user.phone_number
#         token['email'] = user.email
#         token['role'] = user.role
#         token['is_verified'] = user.is_verified

#         if user.phone_number=='':
#             token['registering'] = True
            
#         print(user.role)
#         print(token)
#         return token

# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = MyTokenObtainPairSerializer



# class ForgetPasswordView(APIView):
#     def post(self, request, *args, **kwargs):
#         email = request.data.get('email')
#         user = get_object_or_404(CustomUser, email=email)
#         if user:
#             token = get_random_string(length=20)
#             PasswordResetToken.objects.update_or_create(user=user, defaults={'token': token})
#             print(token)
#             reset_link = f'{url}/reset-password/{token}/'
#             send_mail(
#                 'Reset Your Password [only valid for 24 hours]:',
#                 f'Click the link to reset your password: {reset_link}',
#                 settings.EMAIL_HOST_USER,
#                 [email],
#                 fail_silently=False,
#             )
#             return Response({"message": "Forget password link sended into your Email"}, status=status.HTTP_200_OK)
#         return Response({"message": "Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)    

# class ResetPasswordView(APIView):
#     def post(self, request, *args, **kwargs):
#         try:
#             token = request.data.get('token')
#             new_password = request.data.get('password')
#             print(new_password)
#             print(token)
            
#             token_obj = get_object_or_404(PasswordResetToken, token=token)
            
            
#             current_time = timezone.now()
#             time_difference = current_time - token_obj.created_at

#             if time_difference.total_seconds() > 86400: 
#                 return Response({"message": "Reset token has expired"}, status=status.HTTP_400_BAD_REQUEST)
            
#             user = token_obj.user
#             user.set_password(new_password)
#             user.save()
#             token_obj.delete()
#             print('Password reset successful')
#             return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
        
#         except PasswordResetToken.DoesNotExist:
#             return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        
#         except Exception as e:
#             return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
# class LoginWithGoogleView(APIView):
    
#     def authenticate_or_create_user(self,email,name,password):
#         status = 'existed'
#         try:
#             user = CustomUser.objects.get(email=email)
#             if user.phone_number == '':
#                 status = 'new'
#         except CustomUser.DoesNotExist:
#             user = CustomUser.objects.create_user(username=email, email=email,full_name=name)
#             user.set_password(password[0:10])
#             user.save()
#             print(password)
#             status='new'
            
#         return {'user':user , 'status':status}

#     def get_jwt_token(self,user):
#         token = AccessToken.for_user(user)
#         refresh=RefreshToken.for_user(user)
#         additional_data = {
#             'full_name': user.full_name,
#             'phone_number': user.phone_number,
#             'email': user.email,
#             'role': user.role,
#             'is_verified': user.is_verified,
#         }
#         token.payload.update(additional_data)
#         refresh.payload.update(additional_data)


#         return {'refresh':str(refresh),'access':str(token)}
    
#     def post(self, request, *args, **kwargs):
#         if 'code' in request.data.keys():
#             code = request.data.get('code')
#             id_token = get_id_token_with_code_method_2(code)
#             user_email = id_token.get('email')
#             print(id_token)
#             user = self.authenticate_or_create_user(user_email,id_token.get('name'),id_token.get('at_hash'))
#             print(user)
#             token = self.get_jwt_token(user.get('user'))
#             registering = False
#             if user.get('status') == 'new':
#                 registering = True

#             print(jwt.decode(token.get('access'), algorithms=['HS256'], options={"verify_signature": False}),'this is decoded')
#             print(token)
#             return Response({'access_token': token, 'username': user_email , 'registering' : registering},status=status.HTTP_200_OK)
#         else:  
#             return Response({'message':'Something wrong with google authentication'},status=status.HTTP_400_BAD_REQUEST)
        
# class SaveDataRequestView(APIView):
#     def post(self, request , *args, **kwargs):
#         try:
#             phone_number=request.data.get('phone_number')
#             email=request.data.get('email')
#             if 'password' in request.data.keys():
#                 password = request.data.get('password')
#                 user=get_object_or_404(CustomUser,email=email)
#                 user.phone_number=phone_number
#                 user.set_password(password)
#                 user.save()
#             else:
#                 user=get_object_or_404(CustomUser,email=email)
#                 user.phone_number=phone_number
#                 user.save()
#             return Response({'message':'Data saved successfully'},status=status.HTTP_200_OK)
#         except:
#             return Response({'message':'Something wrong'},status=status.HTTP_400_BAD_REQUEST)


