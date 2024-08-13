from rest_framework import serializers
from .models import CaseModels, UserCases
from api.models import CustomUser, Department

class LawyerDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class CustomUserSerializer(serializers.ModelSerializer):
    departments = LawyerDepartmentSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'full_name', 'profile', 'departments', 'experience']

class CaseModelsSerializer(serializers.ModelSerializer):
    lawyer = CustomUserSerializer(read_only=True)
    department = LawyerDepartmentSerializer(read_only=True)

    class Meta:
        model = CaseModels
        fields = '__all__'

class UserCasesSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    case_model = serializers.PrimaryKeyRelatedField(queryset=CaseModels.objects.all())
    # case_model = CaseModelsSerializer(read_only=True)

    class Meta:
        model = UserCases
        fields = '__all__'
