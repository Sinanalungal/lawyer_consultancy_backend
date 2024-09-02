from rest_framework import serializers
from .models import WalletTransactions

class WalletTransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransactions
        fields = ['pk','amount', 'transaction_type','created_at'] 

class WalletDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransactions
        fields = '__all__'