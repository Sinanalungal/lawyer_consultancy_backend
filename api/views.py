# Standard library imports
from datetime import timedelta
import json
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from schedule.models import BookedAppointment
from wallet.models import WalletTransactions
from django.shortcuts import get_object_or_404


# Third-party imports
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser
from django_redis import get_redis_connection
from twilio.rest import Client

# Local application imports
from .models import CustomUser, PasswordResetToken, Department, Language, States
from server.permissions import IsAdmin, IsLawyer, IsAdminOrLawyer, VerifiedUser
from .serializers import UserRegistrationSerializer, LawyerFilterSerializer, StatesSerializer, LanguageSerializer, PasswordChangeSerializer, DepartmentSerializer, LawyerSerializer, UserUpdateSerializer, UserDetailSerializer, UserDetailForAdminSerializer
from .sms_utils import generate_otp
from .utils import get_id_token_with_code_method_2
from server.constants import url


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer to include additional user information in the token."""

    @classmethod
    def get_token(cls, user):
        """
        Create a token with additional user information.

        Args:
            user (CustomUser): The user instance.

        Returns:
            dict: The JWT token with additional user details.

        Raises:
            PermissionDenied: If the user's account is not verified.
        """
        if user.is_verified:
            token = super().get_token(user)
            token['id'] = user.id
            token['full_name'] = user.full_name
            token['phone_number'] = user.phone_number
            token['email'] = user.email
            token['role'] = user.role
            token['is_verified'] = user.is_verified

            if user.phone_number is None:
                token['registering'] = True

            return token
        else:
            raise PermissionDenied("User account is Blocked.")


class MyTokenObtainPairView(TokenObtainPairView):
    """
    Custom view to obtain JWT tokens with additional user information.
    """
    serializer_class = MyTokenObtainPairSerializer


class LoginWithGoogleView(APIView):
    """
    Handles Google authentication and user creation.

    Methods:
        post: Handle POST request for Google authentication.
    """
    permission_classes = [AllowAny]

    def authenticate_or_create_user(self, email, name, password):
        """
        Authenticate or create a user based on Google authentication details.

        Args:
            email (str): The email address of the user.
            name (str): The full name of the user.
            password (str): The password for the user.

        Returns:
            dict: Contains the user instance and status ('existed' or 'new').
        """
        status = 'existed'
        try:
            user = CustomUser.objects.get(email=email)
            if user.phone_number is None:
                status = 'new'
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(
                username=email, email=email, full_name=name)
            user.set_password(password[:10])
            user.save()
            status = 'new'

        return {'user': user, 'status': status}

    def get_jwt_token(self, user):
        """
        Generate JWT tokens for the user.

        Args:
            user (CustomUser): The user instance.

        Returns:
            dict: Contains the JWT access and refresh tokens with additional user details.

        Raises:
            PermissionDenied: If the user's account is not verified.
        """
        if user.is_verified:
            token = AccessToken.for_user(user)
            refresh = RefreshToken.for_user(user)

            additional_data = {
                'id': user.id,
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
        """
        Handle POST request for Google authentication.

        Args:
            request (Request): The HTTP request containing authentication data.

        Returns:
            Response: Contains the JWT tokens and registration status.
        """
        if 'code' in request.data:
            code = request.data.get('code')
            id_token = get_id_token_with_code_method_2(code)
            print(id_token)
            user_email = id_token.get('email')
            user = self.authenticate_or_create_user(
                user_email, id_token.get('name'), id_token.get('at_hash'))
            token = self.get_jwt_token(user['user'])
            registering = user['status'] == 'new'

            return Response({
                'access_token': token,
                'registering': registering
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Something wrong with Google authentication'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationAPIView(APIView):
    """Handles user registration."""

    def post(self, request, format=None):
        """
        Handle POST request for user registration.

        Args:
            request (Request): The HTTP request containing user registration data.
            format (str, optional): The format of the request data.

        Returns:
            Response: Contains registration status and message.
        """
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
                # obj = MessageHandler(
                #     serializer.validated_data['phone_number'], otp_code)
                # obj.send_otp_via_message()
                subject = 'YOUR OTP'
                message = f'Your Lawyer Link OTP is :{otp_code}'
                recipient_list = [email]
                
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    recipient_list,
                    fail_silently=False,
                )
                return Response({
                    "data": {
                        'email': email,
                        'phone_number': serializer.validated_data['phone_number']
                    },
                    'timer': expiration_time,
                    "message": "OTP sent to your phone number"
                }, status=status.HTTP_200_OK)
            else:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OtpVerificationView(APIView):
    """Handles OTP verification."""

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for OTP verification.

        Args:
            request (Request): The HTTP request containing OTP verification data.

        Returns:
            Response: Contains OTP verification status and message.
        """
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
                            serializer.save()
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
        """
        Handle POST request for resending OTP.

        Args:
            request (Request): The HTTP request containing data for resending OTP.

        Returns:
            Response: Contains the status of OTP resend operation.
        """
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

                # obj = MessageHandler(phone_number, otp_code)
                # obj.send_otp_via_message()

                subject = 'YOUR OTP'
                message = f'Your Lawyer Link OTP is :{otp_code}'
                recipient_list = [email]
                
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    recipient_list,
                    fail_silently=False,
                )

                return Response({
                    "message": "OTP resent successfully",
                    'timer': expiration_time
                }, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({"message": "Please register once again"}, status=status.HTTP_408_REQUEST_TIMEOUT)
        else:
            return Response({"message": "Please register once again"}, status=status.HTTP_408_REQUEST_TIMEOUT)


class MessageHandler:
    """Handles sending OTP messages."""

    def __init__(self, phone_number, otp) -> None:
        self.phone_number = phone_number
        self.otp = otp

    def send_otp_via_message(self):
        """Send OTP via SMS."""
        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=(
                f'Your One Time OTP For Connect Registrations is: {self.otp}. '
                'Do not share this OTP with anyone'
            ),
            from_=settings.TWILIO_PHONE_NUMBER,
            to=f'{settings.COUNTRY_CODE}{self.phone_number}'
        )


class ForgetPasswordView(APIView):
    """Handles forget password functionality."""

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for forget password.

        Args:
            request (Request): The HTTP request containing the email for password reset.

        Returns:
            Response: Contains status and message of the password reset process.
        """
        email = request.data.get('email')
        user = get_object_or_404(CustomUser, email=email)

        if user:
            token = get_random_string(length=20)
            PasswordResetToken.objects.update_or_create(
                user=user,
                defaults={'token': token}
            )
            reset_link = f'{url}/reset-password/{token}/'
            send_mail(
                subject='Reset Your Password [only valid for 24 hours]:',
                message=f'Click the link to reset your password: {reset_link}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

            return Response(
                {"message": "Forget password link sent to your email"},
                status=status.HTTP_200_OK
            )
        return Response(
            {"message": "Something went wrong"},
            status=status.HTTP_400_BAD_REQUEST
        )


class ResetLinkValidationCheck(APIView):
    """Handles validation of the password reset link."""

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for validating the reset link.

        Args:
            request (Request): The HTTP request containing the reset token.

        Returns:
            Response: Contains status and message of the token validation.
        """
        token = request.data.get('token')

        try:
            token_obj = PasswordResetToken.objects.get(token=token)
            current_time = timezone.now()
            time_difference = current_time - token_obj.created_at

            if time_difference.total_seconds() > 86400:
                return Response(
                    {"message": "Invalid token"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {"message": "Valid token"},
                status=status.HTTP_200_OK
            )
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"message": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResetPasswordView(APIView):
    """Handles password reset functionality."""

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for resetting the password.

        Args:
            request (Request): The HTTP request containing the token and new password.

        Returns:
            Response: Contains status and message of the password reset process.
        """
        token = request.data.get('token')
        new_password = request.data.get('password')

        try:
            token_obj = get_object_or_404(PasswordResetToken, token=token)
            current_time = timezone.now()
            time_difference = current_time - token_obj.created_at

            if time_difference.total_seconds() > 86400:
                return Response(
                    {"message": "Reset token has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = token_obj.user
            user.set_password(new_password)
            user.save()
            token_obj.delete()

            return Response(
                {"message": "Password reset successfully"},
                status=status.HTTP_200_OK
            )

        except PasswordResetToken.DoesNotExist:
            return Response(
                {"message": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SaveDataRequestView(APIView):
    """Handles saving user data."""

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for saving user data.

        Args:
            request (Request): The HTTP request containing user data, OTP, and optionally a new password.

        Returns:
            Response: Contains status and message of the data saving process.
        """
        phone_number = request.data.get('phone_number')
        email = request.data.get('email')
        otp = request.data.get('otp')

        redis_conn = get_redis_connection("default")
        stored_otp = redis_conn.get(f"otp_{email}")

        if stored_otp and stored_otp.decode('utf-8') == otp:
            expiration_key = f"expiration_{email}"
            expiration_time = redis_conn.get(expiration_key)
            if expiration_time and float(expiration_time.decode('utf-8')) >= timezone.now().timestamp():
                if 'password' in request.data:
                    password = request.data.get('password')
                    user = get_object_or_404(CustomUser, email=email)
                    user.phone_number = phone_number
                    user.set_password(password)
                    user.save()
                else:
                    user = get_object_or_404(CustomUser, email=email)
                    user.phone_number = phone_number
                    user.save()

                return Response(
                    {'message': 'Data saved successfully'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'message': 'OTP has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'message': 'Invalid OTP'},
                status=status.HTTP_400_BAD_REQUEST
            )


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

            # obj = MessageHandler(phone_number, otp_code)
            # obj.send_otp_via_message()
            subject = 'YOUR OTP'
            message = f'Your Lawyer Link OTP is :{otp_code}'
            recipient_list = [email]
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                recipient_list,
                fail_silently=False,
            )

            return Response(
                {"message": "OTP Resended Successfully", 'timer': expiration_time},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            return Response(
                {"message": "Please Register once again"},
                status=status.HTTP_408_REQUEST_TIMEOUT
            )


class UserDetailView(generics.RetrieveAPIView):
    """ View for user detail information. """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated, VerifiedUser]

    def get_object(self):
        return self.request.user


class UserUpdateView(generics.UpdateAPIView):
    """ view for updating user details """
    queryset = CustomUser.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated, VerifiedUser]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class PasswordUpdate(APIView):
    """Handles updating user passwords."""
    # permission_classes=[IsAuthenticated,VerifiedUser]

    def post(self, request, *args, **kwargs):
        try:
            user_id = request.data.get('user_id')
            recent_password = request.data.get('recent_password')
            new_password = request.data.get('password')
            user = get_object_or_404(CustomUser, id=user_id)

            if user.check_password(recent_password):
                if not check_password(new_password, recent_password):
                    user.set_password(new_password)
                    user.save()
                    return Response(
                        {'message': 'Password Changed Successfully'},
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {'message': 'New password must be different from the recent password'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'message': 'Recent password is invalid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except CustomUser.DoesNotExist:
            return Response(
                {'message': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'message': f'Something went wrong: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class LawyerDetails(APIView):
    """Handles fetching lawyer details."""
    permission_classes = [IsAuthenticated, VerifiedUser]

    def get(self, request, *args, **kwargs):
        try:
            user = CustomUser.objects.filter(
                role='lawyer', is_verified=True
            ).order_by('-experience')[:4]
            serializer = LawyerSerializer(user, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response(
                {'message': 'Lawyers not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'message': f'Something went wrong: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class DepartmentView(APIView):
    """Handles fetching department details."""
    permission_classes = [IsAuthenticated, VerifiedUser]

    def get(self, request, *args, **kwargs):
        try:
            departments = Department.objects.all()
            serializer = DepartmentSerializer(departments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Department.DoesNotExist:
            return Response(
                {'message': 'Departments not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class LawyerFilter(APIView):
    """Handles filtering of lawyers based on criteria."""
    permission_classes = [IsAuthenticated, VerifiedUser]

    def get(self, request, *args, **kwargs):
        try:
            department_name = request.query_params.get('department_name')
            experience = request.query_params.get('experience')
            search_term = request.query_params.get('search_term', '')

            lawyers = CustomUser.objects.filter(
                role='lawyer', is_verified=True
            )

            if department_name:
                lawyers = lawyers.filter(
                    departments__department_name__icontains=department_name
                )

            if experience:
                if experience == '<5':
                    lawyers = lawyers.filter(experience__lt=5)
                elif experience == '5-10':
                    lawyers = lawyers.filter(
                        experience__gte=5, experience__lte=10)
                elif experience == '>10':
                    lawyers = lawyers.filter(experience__gt=10)

            if search_term:
                lawyers = lawyers.filter(full_name__icontains=search_term)

            lawyers = lawyers.order_by('-experience')
            serializer = LawyerFilterSerializer(lawyers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response(
                {'message': 'Lawyers not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'message': f'Something went wrong: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserListAPIView(generics.ListAPIView):

    """
    API view to retrieve a paginated list of users.
    """
    serializer_class = UserDetailForAdminSerializer
    permission_classes = [IsAdmin, VerifiedUser]
    pagination_class = PageNumberPagination
    page_size = 10

    def get_queryset(self):
        queryset = CustomUser.objects.filter(role='user').all()

        # Filter based on is_verified status if provided
        is_verified = self.request.query_params.get('blocked')
        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'
            queryset = queryset.filter(is_verified=not is_verified)

        # Filter based on search query if provided
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )

        return queryset


class UpdateUserVerificationAPIView(generics.UpdateAPIView):
    """
    API view to update user verification status.
    """
    queryset = CustomUser.objects.filter(role='user').all()
    serializer_class = UserDetailForAdminSerializer
    permission_classes = [IsAdmin, VerifiedUser]

    def patch(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        is_verified = request.data.get('is_verified')

        if user_id is None or is_verified is None:
            return Response({'error': 'user_id and is_verified fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.is_verified = is_verified
        user.save()
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class LawyerListAPIView(generics.ListAPIView):
    """
    API view to retrieve a paginated list of users.
    """
    serializer_class = UserDetailForAdminSerializer
    permission_classes = [IsAdmin, VerifiedUser]
    pagination_class = PageNumberPagination
    page_size = 10

    def get_queryset(self):
        queryset = CustomUser.objects.filter(role='lawyer').all()

        is_verified = self.request.query_params.get('blocked')
        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'
            queryset = queryset.filter(is_verified=not is_verified)

        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )

        return queryset


class UpdateLawyerVerificationAPIView(generics.UpdateAPIView):
    """
    API view to update user verification status.
    """
    queryset = CustomUser.objects.filter(role='lawyer').all()
    serializer_class = UserDetailForAdminSerializer
    permission_classes = [IsAdmin, VerifiedUser]

    def patch(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        is_verified = request.data.get('is_verified')

        if user_id is None or is_verified is None:
            return Response({'error': 'user_id and is_verified fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.is_verified = is_verified
        user.save()
        if not user.is_verified:
            for i in BookedAppointment.objects.filter(scheduling__lawyer_profile__user=user):
                latest_transaction = WalletTransactions.objects.filter(
                    user=i.user_profile).order_by('-timestamp').first()
                if latest_transaction.wallet_balance:
                    WalletTransactions.objects.create(user=i.user_profile, payment_details=i.payment_details, wallet_balance=(
                        latest_transaction.wallet_balance + i.scheduling.price), amount=i.scheduling.price, transaction_type='Debit')
                else:
                    WalletTransactions.objects.create(user=i.user_profile, payment_details=i.payment_details,
                                                      wallet_balance=i.scheduling.price, amount=i.scheduling.price, transaction_type='Debit')
                i.is_canceled = True
                i.save()
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class UserProfileImageUpdateView(APIView):
    """
    user profile image updation

    """
    permission_classes = [IsAuthenticated, VerifiedUser]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()

        if 'profile_image' in data and data['profile_image'] in ['', 'null']:
            data['profile_image'] = None

        serializer = UserDetailSerializer(user, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            if 'profile_image' in response_data:
                if response_data['profile_image']:
                    response_data['profile_image'] = request.build_absolute_uri(
                        response_data['profile_image'])
                else:
                    response_data['profile_image'] = None
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_success_headers(self, data):
        """
        Implement this method to return any custom headers you want to include in the response.
        """
        return {}


class PasswordChangeView(APIView):
    """
    password changing api view
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepartmentLanguageStateView(APIView):
    """
    View to fetch departments, languages, and states.
    """

    def get(self, request, *args, **kwargs):
        departments = Department.objects.all()
        languages = Language.objects.all()
        states = States.objects.all()

        department_serializer = DepartmentSerializer(departments, many=True)
        language_serializer = LanguageSerializer(languages, many=True)
        states_serializer = StatesSerializer(
            states, many=True)

        return Response({
            'departments': department_serializer.data,
            'languages': language_serializer.data,
            'states': states_serializer.data
        })
