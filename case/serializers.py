from rest_framework import serializers
from .models import Case,SelectedCases,AllotedCases
from api.models import LawyerProfile, Department, Language,States,CustomUser

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['department_name']

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['name']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields =['id','full_name','profile_image']

class LawyerProfileSerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = LawyerProfile
        fields = ['id','user', 'departments', 'experience', 'description', 'languages', 'address', 'city', 'state', 'postal_code']

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = States
        fields = ['id', 'name']

class CaseSerializer(serializers.ModelSerializer):
    state_name = serializers.SerializerMethodField() 
    state = serializers.PrimaryKeyRelatedField(queryset=States.objects.all()) 
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True) 
    user_phone = serializers.IntegerField(source='user.phone_number', read_only=True) 

    class Meta:
        model = Case
        fields = ['id', 'case_type', 'description', 'budget', 'status', 'reference_until', 'state', 'state_name', 'user_name', 'user_email','user_phone']
        read_only_fields = ['id', 'status', 'state_name', 'user_name', 'user_email','user_phone']

    def get_state_name(self, obj):
        return obj.state.name


class SelectedCasesSerializer(serializers.ModelSerializer):
    lawyer = LawyerProfileSerializer(read_only=True) 
    class Meta:
        model = SelectedCases
        fields = ['id', 'lawyer', 'case_model', 'created_at']
        read_only_fields = ['id', 'created_at', 'lawyer']

class SelectedCasesAllotedSerializer(serializers.ModelSerializer):
    lawyer = LawyerProfileSerializer(read_only=True) 
    case_model = CaseSerializer(read_only=True) 
    class Meta:
        model = SelectedCases
        fields = ['id', 'lawyer', 'case_model', 'created_at']
        read_only_fields = ['id', 'created_at', 'lawyer']


class AllotedCasesSerializer(serializers.ModelSerializer):
    selected_case = SelectedCasesAllotedSerializer(read_only=True)
    class Meta:
        model = AllotedCases
        fields = ['id', 'selected_case', 'status', 'created_at']
        read_only_fields = ['id','created_at','status']

class AllotedCasesSerializerForAdmin(serializers.ModelSerializer):
    class Meta:
        model = AllotedCases
        fields = '__all__'
        depth = 1  # This will allow nested relationships to be serialized