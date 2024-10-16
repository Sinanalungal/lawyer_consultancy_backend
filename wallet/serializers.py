from rest_framework import serializers
from .models import WalletTransactions, WithdrawingRequests
from api.models import CustomUser


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


class UserWalletDetailSerializerForAdmin(serializers.ModelSerializer):
    wallet_balance = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email', 'wallet_balance']

    def get_wallet_balance(self, user):
        # Get the latest WalletTransactions object for the user
        latest_transaction = WalletTransactions.objects.filter(user=user).order_by('-created_at').first()
        return latest_transaction.wallet_balance if latest_transaction else 0.00  