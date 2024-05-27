from rest_framework import serializers
from .models import SubscriptionPlanModels

class SubscriptionPlanModelsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionPlanModels
        fields = '__all__'
