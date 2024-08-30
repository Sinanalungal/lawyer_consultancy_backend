from rest_framework import serializers
from .models import Case  # Make sure you import your Case model
from api.models import States

# class CaseSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Case
#         fields = ['id', 'case_type', 'description', 'budget', 'status', 'reference_until', 'state']
#         read_only_fields = ['id', 'status']


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = States
        fields = ['id', 'name']

class CaseSerializer(serializers.ModelSerializer):
    state_name = serializers.SerializerMethodField()  # Read-only field for state name
    state = serializers.PrimaryKeyRelatedField(queryset=States.objects.all())  # For writing state as ID

    class Meta:
        model = Case
        fields = ['id', 'case_type', 'description', 'budget', 'status', 'reference_until', 'state', 'state_name']
        read_only_fields = ['id', 'status', 'state_name']

    def get_state_name(self, obj):
        return obj.state.name  # This returns the name of the state
