from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import WalletTransactions
from django.db.models import Sum
from .serializers import WalletTransactionsSerializer,WalletDataSerializer
from django.conf import settings
import stripe
from rest_framework.permissions import IsAuthenticated
from server.permissions import VerifiedUser

class AddFundsView(APIView):
    permission_classes = [IsAuthenticated,VerifiedUser]
    def post(self, request, *args, **kwargs):
        
        amount = int(request.data.get('amount'))
        print(amount, 'amount')
        if amount <= 0:
            return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

    
        session_price = (int(amount) * 100)
        try:
            checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {
                            'name': f"Adding Fund",
                        },
                        'unit_amount': session_price,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=(settings.DOMAIN_URL + 'user/wallet/' + '?success={CHECKOUT_SESSION_ID}')
                        if request.user.role == 'user' else 
                        (settings.DOMAIN_URL + 'lawyer/wallet/' + '?success={CHECKOUT_SESSION_ID}') if request.user.role == 'lawyer' else (settings.DOMAIN_URL + 'admin/wallet/' + '?success={CHECKOUT_SESSION_ID}') ,
            cancel_url=(settings.DOMAIN_URL + 'user/wallet/' + '?cancel={CHECKOUT_SESSION_ID}')
                        if request.user.role == 'user' else 
                        (settings.DOMAIN_URL + 'lawyer/wallet/' + '?cancel={CHECKOUT_SESSION_ID}') if request.user.role == 'lawyer' else (settings.DOMAIN_URL + 'admin/wallet/' + '?cancel={CHECKOUT_SESSION_ID}'),
            metadata={
                'user_id': request.user.id,
                'payment_for': 'wallet',
            }
        )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'sessionId':checkout_session.id}, status=status.HTTP_200_OK)

class GetBalanceView(APIView):
    permission_classes = [IsAuthenticated,VerifiedUser]
    def get(self, request, *args, **kwargs):
        try:
            latest_transaction = WalletTransactions.objects.filter(user=request.user).latest('created_at')
            total_balance = latest_transaction.wallet_balance
        except WalletTransactions.DoesNotExist:
            total_balance = 0
        balance_history = WalletTransactions.objects.filter(user=request.user).order_by('-created_at').all()
        balance_data = WalletTransactionsSerializer(balance_history, many=True).data
        return Response({"balance": total_balance, 'balance_history': balance_data}, status=status.HTTP_200_OK)
    
    
class WithdrawFundsView(APIView):
    permission_classes = [IsAuthenticated,VerifiedUser]
    def post(self, request, *args, **kwargs):
        serializer = WalletDataSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data.get('amount')
            if amount <= 0:
                return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

            total_balance = WalletTransactions.objects.filter(transaction_type='credit').aggregate(Sum('amount'))['amount__sum'] or 0
            if amount > total_balance:
                return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

            WalletTransactions.objects.create(
                wallet_balance=-amount,
                amount=amount,
                transaction_type='debit'
            )
            return Response({"message": "Funds withdrawn successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)