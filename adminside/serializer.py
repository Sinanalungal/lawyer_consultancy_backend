from rest_framework import serializers
from api.models import CustomUser
from password_generator import PasswordGenerator
from api.models import Department
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage





class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser model.
    """

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'full_name','profile', 'phone_number', 'role', 'is_verified')

class LawyerSerializer(serializers.ModelSerializer):
    profile = serializers.ImageField(required=False)
    document = serializers.ImageField(required=False)
    departments = serializers.ListField(
        child=serializers.CharField(), write_only=True
    )

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'document', 'departments', 'experience', 'description', 'profile']
        extra_kwargs = {
            'role': {'default': 'lawyer'},
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        departments_data = validated_data.pop('departments')
        print(departments_data)
        
        # Generate a password using the PasswordGenerator
        pwo = PasswordGenerator()
        pwo.excludeschars = "[]{}()<>+-_="
        pwo.minnumbers = 1
        pwo.minschars= 1
        pwo.minuchars = 1
        pwo.minlchars = 1
        pwo.minlen = 8
        pwo.maxlen = 16
        password = pwo.generate()
        print(password)
        
        # Create the user
        user = CustomUser.objects.create_user(
            username=validated_data['email'],
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            password=password,
            role='lawyer',
            profile=validated_data.get('profile', None),
            document=validated_data.get('document', None),
            is_verified=True
        )
        
        user.experience = validated_data.get('experience', 0)
        user.description = validated_data.get('description', '')
        user.save()
        
        # Associate departments with the user
        if departments_data:
            for department_name in departments_data:
                print(department_name)
                for department in department_name.split(','):
                    department, created = Department.objects.get_or_create(department_name=department)
                    print(department)
                    user.departments.add(department)
        

        subject = ' Welcome to Lawyer Consultancy - Your Consultancy Account Details'
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

        return user
    

class DepartmentForm(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'