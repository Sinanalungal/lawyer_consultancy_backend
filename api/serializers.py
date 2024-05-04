from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import CustomUser


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



# class PasswordSerializer(serializers.Serializer):

#     password = serializers.CharField()

#     def validate_password(self, value):

#         if len(value) < 8:
#             raise serializers.ValidationError("Password must be at least 8 characters long.")

#         if not any(char.isalpha() for char in value):
#             raise serializers.ValidationError("Password must contain at least one letter.")
        

#         if not any(char.isdigit() for char in value):
#             raise serializers.ValidationError("Password must contain at least one digit.")

#         special_chars = "!@#$%^&*()_+{}|:\"<>?`\-=[\];',./"
#         if not any(char in special_chars for char in value):
#             raise serializers.ValidationError("Password must contain at least one special character.")

#         return value
