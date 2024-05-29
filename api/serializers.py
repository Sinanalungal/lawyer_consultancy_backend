from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import CustomUser,Department
import re


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Fields:
    - password: write-only CharField
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'password', 'role', 'is_verified']

    def create(self, validated_data):
        """
        Create a new user based on validated data.

        Args:
        - validated_data: Validated data containing user details.

        Returns:
        - CustomUser: Newly created user instance.
        """
        role = validated_data.get('role', 'user')
        user = CustomUser.objects.create_user(
            username=validated_data['email'],
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            role=role,
        )
        return user
    
    
class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','full_name', 'email', 'phone_number', 'role', 'profile']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class UserUpdateSerializer(serializers.ModelSerializer):
    # password = serializers.CharField(write_only=True)
    profile = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'role', 'profile']

    # def update(self, instance, validated_data):
    # # Handle password separately to hash it before saving
    #     if 'password' in validated_data and validated_data['password'] != '':
    #         password = validated_data.pop('password')
    #         if password and re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[$@$!%*#?&])[A-Za-z\d$@$!%*#?&]{8,}$', password):
    #             instance.set_password(password)  # Hash the password using Django's set_password method

    #     return super().update(instance, validated_data)
    
class LawyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','full_name', 'departments', 'experience', 'description', 'profile']


class LawyerFilterSerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)
    class Meta:
        model = CustomUser
        fields = ['id','full_name', 'departments', 'experience', 'description', 'profile']


class OtpSerializer(serializers.Serializer):
    """
    Serializer for OTP validation.
    
    Fields:
    - otp: IntegerField

    Methods:
    - validate_otp: Validates that the OTP is a 6-digit number.
    """
    otp = serializers.IntegerField()

    def validate_otp(self, value):
        """
        Validate that the OTP is a 6-digit number.

        Args:
        - value: OTP value to validate.

        Returns:
        - int: Validated OTP value.

        Raises:
        - ValidationError: If the OTP is not a 6-digit number.
        """
        if len(str(value)) != 6:
            raise ValidationError("OTP must be a 6-digit number.")
        return value
