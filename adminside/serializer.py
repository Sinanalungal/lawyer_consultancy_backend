from rest_framework import serializers
from api.models import CustomUser,LawyerProfile



class LawyerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name','username', 'email', 'phone_number', 'role', 'profile_image']
        
# class LawyerProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LawyerProfile
#         fields = ['id', 'user', 'experience', 'description', 'departments', 'languages']
#         read_only_fields = ['departments', 'languages']

class LawyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawyerProfile
        fields = ['id', 'user', 'experience', 'description', 'departments', 'languages', 'address', 'city', 'state', 'postal_code']
        read_only_fields = ['departments', 'languages']
