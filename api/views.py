from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer,LawyerFilterSerializer,DepartmentSerializer,LawyerSerializer, OtpSerializer,UserUpdateSerializer,UserDetailSerializer
from django_redis import get_redis_connection
from .sms_utils import generate_otp
import json
from django.conf import settings
from twilio.rest import Client
# from rest_framework.permissions import IsAuthenticated  
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from .models import CustomUser, PasswordResetToken,Department
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from server.constants import url
from .utils import get_id_token_with_code_method_1, get_id_token_with_code_method_2
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework.permissions import AllowAny
from django.core.exceptions import PermissionDenied
from rest_framework import generics
from django.contrib.auth import authenticate,hashers
from django.contrib.auth.hashers import check_password






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
        if user.is_verified:
            token = super().get_token(user)
            token['id'] = user.id
            token['full_name'] = user.full_name
            token['phone_number'] = user.phone_number
            token['email'] = user.email
            token['role'] = user.role
            token['is_verified'] = user.is_verified

            if user.phone_number == '':
                token['registering'] = True

            return token
        else:
            raise PermissionDenied("User account is Blocked.")


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class ForgetPasswordView(APIView):
    """Handles forget password functionality."""

    def post(self, request, *args, **kwargs):
        """Handle POST request for forget password."""
        email = request.data.get('email')
        user = get_object_or_404(CustomUser, email=email)
        if user:
            # redis_conn = get_redis_connection("default")
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
            
            # redis_conn.setex(token, 86400, token)

            return Response({"message": "Forget password link sended into your Email"}, status=status.HTTP_200_OK)
        return Response({"message": "Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)


class ResetLinkValidationCheck(APIView):
    
    def post(self, request, *args, **kwargs):
        try:
            token = request.data.get('token')
            # token_obj = get_object_or_404(PasswordResetToken, token=token)
            token_obj = PasswordResetToken.objects.get(token=token)
            current_time = timezone.now()
            time_difference = current_time - token_obj.created_at

            if time_difference.total_seconds() > 86400:
                return Response({"message": "Invalid Token"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({"message": "Valid Token"}, status=status.HTTP_200_OK)
        except PasswordResetToken.DoesNotExist:
            return Response({"message": "Invalid Token"}, status=status.HTTP_400_BAD_REQUEST)

        


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
    permission_classes = [AllowAny]  # Allow unrestricted access

    """Handles Google authentication."""

    def authenticate_or_create_user(self, email, name, password):
        status = 'existed'
        try:
            
            user = CustomUser.objects.get(email=email)
            if user.phone_number == None:
                status = 'new'
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(username=email, email=email, full_name=name)
            user.set_password(password[0:10])
            user.save()
            status = 'new'

        return {'user': user, 'status': status}

    def get_jwt_token(self, user):
        if user.is_verified:
            token = AccessToken.for_user(user)
            refresh = RefreshToken.for_user(user)
            additional_data = {
                'id':user.id,
                'full_name': user.full_name,
                'phone_number': user.phone_number,
                'email': user.email,
                'role': user.role,
                'is_verified': user.is_verified,
            }
            token.payload.update(additional_data)
            refresh.payload.update(additional_data)

            return {'refresh': str(refresh), 'access': str(token)}
        else:
            raise PermissionDenied('User account is Blocked')

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
            print(token)
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
        except ValueError: 
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
        


class UserDetailView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserDetailSerializer
    # Optional: Add permissions if needed

class UserUpdateView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserUpdateSerializer
    # Optional: Add permissions if needed

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
class PasswordUpdate(APIView):
    def post(self, request, *args, **kwargs):
        try:
            user_id = request.data.get('user_id')
            recent_password = request.data.get('recent_password')
            new_password = request.data.get('password')
            user = get_object_or_404(CustomUser, id=user_id)
            

            if user.check_password(recent_password):
                print(check_password(new_password, recent_password))
                if not check_password(new_password, recent_password):
                    user.set_password(new_password)
                    user.save()
                    return Response({'message': 'Password Changed Successfully'}, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'New password must be different from the recent password'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'message': 'Recent password is invalid'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': 'Something went wrong: {}'.format(str(e))}, status=status.HTTP_400_BAD_REQUEST)


class LawyerDetails(APIView):
    def get(self, request,*args, **kwargs):
        try:
            user = CustomUser.objects.filter(role='lawyer', is_verified=True).order_by('-experience')[:4]
            serializer = LawyerSerializer(user,many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'message': 'Lawyers not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': 'Something went wrong: {}'.format(str(e))}, status=status.HTTP_400_BAD_REQUEST)
        
class DepartmentView(APIView):
    def get(self,request,*args, **kwargs):
        try:
            departments = Department.objects.all()
            serializer = DepartmentSerializer(departments,many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Department.DoesNotExist:
            return Response({'message': 'Departments not found'}, status=status.HTTP_404_NOT_FOUND)
        


class LawyerFilter(APIView):
    def get(self, request, *args, **kwargs):
        try:
            department_name = request.query_params.get('department_name')
            experience = request.query_params.get('experience')
            search_term = request.query_params.get('search_term', '')

            lawyers = CustomUser.objects.filter(role='lawyer', is_verified=True)

            if department_name:
                lawyers = lawyers.filter(departments__department_name__icontains=department_name)

            if experience:
                if experience == '<5':
                    lawyers = lawyers.filter(experience__lt=5)
                elif experience == '5-10':
                    lawyers = lawyers.filter(experience__gte=5, experience__lte=10)
                elif experience == '>10':
                    lawyers = lawyers.filter(experience__gt=10)

            if search_term:
                lawyers = lawyers.filter(
                    full_name__icontains=search_term
                )
            lawyers = lawyers.order_by('-experience')
            serializer = LawyerFilterSerializer(lawyers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'message': 'Lawyers not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': f'Something went wrong: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)