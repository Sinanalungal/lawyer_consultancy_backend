from rest_framework import serializers
from api.models import LawyerProfile, Department, Language


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['department_name']


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['name']


class LawyerProfileSerializer(serializers.ModelSerializer):
    user_pk = serializers.CharField(source='user.pk')
    user_full_name = serializers.CharField(source='user.full_name')
    user_profile_image = serializers.ImageField(source='user.profile_image')
    # user_email = serializers.EmailField(source='user.email')
    # user_phone_number = serializers.CharField(source='user.phone_number')
    departments = DepartmentSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = LawyerProfile
        fields = [
            'pk',
            'user_pk',
            'user_full_name',
            'user_profile_image',
            # 'user_email',
            # 'user_phone_number',
            'departments',
            'experience',
            'description',
            'languages',
            'address',
            'city',
            'state',
            'postal_code',
        ]
