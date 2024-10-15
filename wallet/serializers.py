from rest_framework import serializers
from .models import WalletTransactions, WithdrawingRequests


class WalletTransactionsSerializer(serializers.ModelSerializer):
    """Serializer for WalletTransactions model."""

    class Meta:
        model = WalletTransactions
        fields = ['pk', 'amount', 'transaction_type', 'created_at']


class WalletDataSerializer(serializers.ModelSerializer):
    """Serializer for all fields of WalletTransactions model."""

    class Meta:
        model = WalletTransactions
        fields = '__all__'


class WithdrawingRequestSerializer(serializers.ModelSerializer):
    """Serializer for WithdrawingRequests model."""

    class Meta:
        model = WithdrawingRequests
        fields = '__all__'
