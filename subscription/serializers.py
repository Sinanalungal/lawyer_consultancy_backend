from rest_framework import serializers
from .models import SubscriptionPlanModels,SubscriptionPlan

class SubscriptionPlanModelsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionPlanModels
        fields = '__all__'

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanModelsSerializer()
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
