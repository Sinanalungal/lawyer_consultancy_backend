from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from server.permissions import IsAdmin, VerifiedUser
from api.models import CustomUser, Department, Language
from .serializer import LawyerRegistrationSerializer, LawyerProfileSerializer
from rest_framework.views import APIView
from django.db import transaction
from password_generator import PasswordGenerator
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status


class AddLawyerView(APIView):
    """
    API view to handle the addition of a lawyer.

    This view handles the creation of a CustomUser with the role of 'lawyer'
    and their associated LawyerProfile, including departments, languages,
    and other related data.
    """
    permission_classes = [IsAdmin, VerifiedUser]

    def post(self, request):
        try:
            with transaction.atomic():
                # Generate a password
                pwo = PasswordGenerator()
                pwo.excludeschars = "[]{}()<>+-_="
                pwo.minnumbers = 1
                pwo.minschars = 1
                pwo.minuchars = 1
                pwo.minlchars = 1
                pwo.minlen = 8
                pwo.maxlen = 16
                password = pwo.generate()

                # Extract user data
                user_data = {
                    'full_name': request.data.get('full_name'),
                    'email': request.data.get('email'),
                    'username': request.data.get('email'),
                    'phone_number': request.data.get('phone_number'),
                    'role': 'lawyer',
                    'profile_image': request.FILES.get('profile_image'),
                }

                # Validate user data with the serializer
                user_serializer = LawyerRegistrationSerializer(data=user_data)
                user_serializer.is_valid(raise_exception=True)

                # Create a new user instance but don't save to the database yet
                user = user_serializer.save()
                user.set_password(password)  # Hash the password
                user.save()  # Save the user instance

                # Extract profile data
                profile_data = {
                    'user': user.id,
                    'experience': request.data.get('experience'),
                    'description': request.data.get('description'),
                    'address': request.data.get('address'),
                    'city': request.data.get('city'),
                    'state': request.data.get('state'),
                    'postal_code': request.data.get('postal_code'),
                }

                # Create the lawyer profile
                profile_serializer = LawyerProfileSerializer(data=profile_data)
                profile_serializer.is_valid(raise_exception=True)
                lawyer_profile = profile_serializer.save()

                # Handle departments (ManyToManyField)
                department_ids = request.data.get('department', [])
                if department_ids:
                    if isinstance(department_ids, str):
                        department_ids = department_ids.strip('[]').split(',')
                        department_ids = [
                            int(dept_id) for dept_id in department_ids if dept_id.strip().isdigit()]
                    departments = Department.objects.filter(
                        id__in=list(department_ids))
                    lawyer_profile.departments.set(departments)

                # Handle languages (ManyToManyField)
                language_ids = request.data.get('language', [])
                if language_ids:
                    if isinstance(language_ids, str):
                        language_ids = language_ids.strip('[]').split(',')
                        language_ids = [
                            int(lang_id) for lang_id in language_ids if lang_id.strip().isdigit()]
                    languages = Language.objects.filter(id__in=language_ids)
                    lawyer_profile.languages.set(languages)

                # Send the welcome email
                subject = 'Welcome to Lawyer Consultancy - Your Consultancy Account Details'
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [user.email]

                text_content = f"""Dear {user.full_name},

                I hope this email finds you well.

                I am pleased to inform you that you have been added as a consultant on our Lawyer Consultancy website. Your expertise and insights will be invaluable to our clients, and we are delighted to have you on board.

                Below are your account credentials:
                Email: {user.email}
                Password: {password}

                You can log in to your account using the provided credentials. Upon login, we encourage you to change your password to something more memorable. Your security is important to us.

                Once logged in, you will have access to various features and functionalities, including scheduling sessions with clients. Feel free to take sessions at your convenience, and provide your expertise to those seeking legal assistance.

                Should you have any questions or require assistance, please don't hesitate to reach out to us. We are here to support you every step of the way.

                Thank you for joining our platform, and we look forward to a fruitful collaboration.

                Best regards,
                Lawyer Consultancy
                """

                send_mail(subject, text_content, from_email, recipient_list)

                return Response({
                    'user': user_serializer.data,
                    'profile': profile_serializer.data
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
