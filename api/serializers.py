from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import CustomUser,Department,LawyerProfile,Language


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
    
    
# class UserDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['id','full_name', 'email', 'phone_number', 'role', 'profile_image']

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'profile_image']
        extra_kwargs = {
            'profile_image': {'required': False},
        }

class UserDetailForAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['pk','full_name', 'email', 'phone_number', 'profile_image', 'is_verified', 'created_at']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class UserUpdateSerializer(serializers.ModelSerializer):
    # password = serializers.CharField(write_only=True)
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'profile_image']

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
        fields = ['id','full_name', 'departments', 'experience', 'description', 'profile_image']


class LawyerFilterSerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)
    class Meta:
        model = CustomUser
        fields = ['id','full_name', 'departments', 'experience', 'description', 'profile_image']


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


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = self.context['request'].user
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')
        
        if not user.check_password(current_password):
            raise serializers.ValidationError({"current_password": "Current password is incorrect"})
        
        if new_password != confirm_new_password:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match"})
        
        return attrs
    
    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()


# class LawyerRegistrationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['id', 'full_name','username', 'email', 'phone_number', 'role', 'profile_image']

# class LawyerProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LawyerProfile
#         fields = ['id', 'user', 'experience', 'description', 'departments', 'languages']
#         read_only_fields = ['departments', 'languages']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'department_name']

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name']