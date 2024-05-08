from rest_framework import serializers
from api.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser model.
    """

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'full_name', 'phone_number', 'role', 'is_verified')
