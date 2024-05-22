from rest_framework import serializers
from api.models import CustomUser
from password_generator import PasswordGenerator
from api.models import Department


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser model.
    """

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'full_name', 'phone_number', 'role', 'is_verified')

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
        
        return user
class DepartmentForm(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'