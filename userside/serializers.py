from rest_framework import serializers
from api.models import LawyerProfile, Department, Language


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for the Department model."""

    class Meta:
        model = Department
        fields = ['department_name']


class LanguageSerializer(serializers.ModelSerializer):
    """Serializer for the Language model."""

    class Meta:
        model = Language
        fields = ['name']


class LawyerProfileSerializer(serializers.ModelSerializer):
    """Serializer for the LawyerProfile model, including related user information."""

    user_pk = serializers.CharField(source='user.pk')
    user_full_name = serializers.CharField(source='user.full_name')
    user_profile_image = serializers.ImageField(source='user.profile_image')
    departments = DepartmentSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = LawyerProfile
        fields = [
            'pk',
            'user_pk',
            'user_full_name',
            'user_profile_image',
            'departments',
            'experience',
            'description',
            'languages',
            'address',
            'city',
            'state',
            'postal_code',
        ]
