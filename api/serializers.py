from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import CustomUser
# class UserRegistrationSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)

#     class Meta:
#         model = CustomUser
#         fields = ['full_name','email', 'phone_number', 'password','role' ]

#     def create(self, validated_data):
#         role = validated_data.get('role', 'user')
#         if role == 'user':
#             user = CustomUser.objects.create_user(
#                 username=validated_data['email'],
#                 full_name=validated_data['full_name'],
#                 email=validated_data['email'],
#                 phone_number=validated_data['phone_number'],
#                 password=validated_data['password'],
#                 role=role,
#                 is_verified=False 
#             )
#         else:
#             user = CustomUser.objects.create_user(
#                 username=validated_data['email'],
#                 full_name=validated_data['full_name'],
#                 email=validated_data['email'],
#                 phone_number=validated_data['phone_number'],
#                 password=validated_data['password'],
#                 role=role
#             )
#         return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'password', 'role','is_verified']
    
    def create(self, validated_data):
        role = validated_data.get('role', 'user')
        if role == 'user':
            user = CustomUser.objects.create_user(
                username=validated_data['email'],
                full_name=validated_data['full_name'],
                email=validated_data['email'],
                phone_number=validated_data['phone_number'],
                password=validated_data['password'],
                role=role,
            )
        else:
            user = CustomUser.objects.create_user(
                username=validated_data['email'],
                full_name=validated_data['full_name'],
                email=validated_data['email'],
                phone_number=validated_data['phone_number'],
                password=validated_data['password'],
                role=role
            )
        return user



class OtpSerializer(serializers.Serializer):
    otp = serializers.IntegerField()

    def validate_otp(self, value):
        """
        Validate that the OTP is a 6-digit number.
        """
        if len(str(value)) != 6:
            raise ValidationError("OTP must be a 6-digit number.")
        return value

