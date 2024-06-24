from rest_framework import serializers
from .models import SubscriptionPlanModels,SubscriptionPlan,Subscription
from api.serializers import LawyerFilterSerializer
class SubscriptionPlanModelsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionPlanModels
        fields = '__all__'

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanModelsSerializer()
    lawyer = LawyerFilterSerializer()
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer()
    class Meta:
        model = Subscription
        fields = '__all__'