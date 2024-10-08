from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import WalletTransactions, WithdrawingRequests, PaymentDetails
from django.db.models import Sum
from .serializers import WithdrawingRequestSerializer, WalletTransactionsSerializer, WalletDataSerializer
from django.conf import settings
import stripe
from rest_framework.permissions import IsAuthenticated
from server.permissions import VerifiedUser
from django.templatetags.static import static
import uuid
from rest_framework import viewsets
from decimal import Decimal
from django.db import transaction


class AddFundsView(APIView):
    permission_classes = [IsAuthenticated, VerifiedUser]

    def post(self, request, *args, **kwargs):

        amount = int(request.data.get('amount'))
        print(amount, 'amount')
        if amount <= 0:
            return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        image_url = request.build_absolute_uri(
            static('images/add-to-wallet.png'))

        session_price = (int(amount) * 100)
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': 'Add Money to Wallet',
                                'description':  f"Add money to the wallet by fullfilling the payment",
                                # 'images': [image_url],
                            },
                            'unit_amount': session_price,
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=(settings.DOMAIN_URL + 'user/wallet/' + \
                             '?success={CHECKOUT_SESSION_ID}')
                if request.user.role == 'user' else
                (settings.DOMAIN_URL + 'lawyer/wallet/' + '?success={CHECKOUT_SESSION_ID}') if request.user.role == 'lawyer' else (
                    settings.DOMAIN_URL + 'admin/wallet/' + '?success={CHECKOUT_SESSION_ID}'),
                cancel_url=(settings.DOMAIN_URL + 'user/wallet/' + \
                            '?cancel={CHECKOUT_SESSION_ID}')
                if request.user.role == 'user' else
                (settings.DOMAIN_URL + 'lawyer/wallet/' + '?cancel={CHECKOUT_SESSION_ID}') if request.user.role == 'lawyer' else (
                    settings.DOMAIN_URL + 'admin/wallet/' + '?cancel={CHECKOUT_SESSION_ID}'),
                metadata={
                    'user_id': request.user.id,
                    'payment_for': 'wallet',
                }
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'sessionId': checkout_session.id}, status=status.HTTP_200_OK)


class GetBalanceView(APIView):
    permission_classes = [IsAuthenticated, VerifiedUser]

    def get(self, request, *args, **kwargs):
        try:
            latest_transaction = WalletTransactions.objects.filter(
                user=request.user).latest('created_at')
            total_balance = latest_transaction.wallet_balance
        except WalletTransactions.DoesNotExist:
            total_balance = 0
        balance_history = WalletTransactions.objects.filter(
            user=request.user).order_by('-created_at').all()
        balance_data = WalletTransactionsSerializer(
            balance_history, many=True).data
        return Response({"balance": total_balance, 'balance_history': balance_data}, status=status.HTTP_200_OK)


class WithdrawFundsView(APIView):
    permission_classes = [IsAuthenticated, VerifiedUser]

    def post(self, request, *args, **kwargs):
        serializer = WalletDataSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data.get('amount')
            if amount <= 0:
                return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

            total_balance = WalletTransactions.objects.filter(
                transaction_type='credit').aggregate(Sum('amount'))['amount__sum'] or 0
            if amount > total_balance:
                return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

            WalletTransactions.objects.create(
                wallet_balance=-amount,
                amount=amount,
                transaction_type='debit'
            )
            return Response({"message": "Funds withdrawn successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WithdrawMoney(APIView):
    permission_classes = [IsAuthenticated, VerifiedUser]

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            amount = request.data.get('amount')
            upi_id = request.data.get('upi_id')

            # Check if amount is valid
            if not amount or Decimal(amount) <= 0:
                return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the latest wallet transaction
            latest_transaction = WalletTransactions.objects.filter(
                user=request.user).order_by('-created_at').first()
            latest_wallet_balance = latest_transaction.wallet_balance if latest_transaction else 0

            # Ensure the user has sufficient balance
            if latest_wallet_balance < Decimal(amount):
                return Response({"error": "Insufficient wallet balance."}, status=status.HTTP_400_BAD_REQUEST)

            # Generate UUID for transaction
            uuid_for_payment = uuid.uuid4()

            try:
                # Create payment details
                payment_details = PaymentDetails.objects.create(
                    payment_method='upi',
                    transaction_id=str(uuid_for_payment),
                    payment_for='withdraw_to_wallet'
                )

                # Update wallet balance and record the transaction
                WalletTransactions.objects.create(
                    user=request.user,
                    wallet_balance=latest_wallet_balance - Decimal(amount),
                    amount=Decimal(amount),
                    transaction_type='debit',
                    payment_details=payment_details
                )

                # Create a withdrawing request
                WithdrawingRequests.objects.create(
                    user=request.user, amount=Decimal(amount), upi_id=upi_id)

                return Response({"message": "Withdrawal requested successfully."}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawingRequestsViewSet(viewsets.ModelViewSet):
    queryset = WithdrawingRequests.objects.all()
    serializer_class = WithdrawingRequestSerializer

    def get_queryset(self):
        status = self.request.query_params.get('status', None)
        if status:
            return self.queryset.filter(status=status)
        return self.queryset
