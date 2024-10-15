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
    """
    View to add funds to the wallet.
    Creates a Stripe checkout session for adding funds to the user's wallet.
    """
    permission_classes = [IsAuthenticated, VerifiedUser]

    def post(self, request, *args, **kwargs):
        amount = int(request.data.get('amount'))
        print(amount, 'amount')

        if amount <= 0:
            return Response({"error": "Amount must be greater than zero."},
                            status=status.HTTP_400_BAD_REQUEST)

        image_url = request.build_absolute_uri(static('images/add-to-wallet.png'))

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
                                'description': "Add money to the wallet by fulfilling the payment",
                            },
                            'unit_amount': session_price,
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=(settings.DOMAIN_URL + 'user/success' + '?checkout_id={CHECKOUT_SESSION_ID}')
                if request.user.role == 'user' else
                (settings.DOMAIN_URL + 'lawyer/success' + '?checkout_id={CHECKOUT_SESSION_ID}'),
                cancel_url=(settings.DOMAIN_URL + 'user/fail/')
                if request.user.role == 'user' else
                (settings.DOMAIN_URL + 'lawyer/fail/'),
                metadata={
                    'user_id': request.user.id,
                    'payment_for': 'wallet',
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'sessionId': checkout_session.id}, status=status.HTTP_200_OK)


class GetBalanceView(APIView):
    """
    View to get the current wallet balance and transaction history.
    """
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
        balance_data = WalletTransactionsSerializer(balance_history, many=True).data

        return Response({"balance": total_balance, 'balance_history': balance_data},
                        status=status.HTTP_200_OK)


class WithdrawFundsView(APIView):
    """
    View to withdraw funds from the wallet.
    Validates if the withdrawal amount is allowed and processes the withdrawal.
    """
    permission_classes = [IsAuthenticated, VerifiedUser]

    def post(self, request, *args, **kwargs):
        serializer = WalletDataSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data.get('amount')
            if amount <= 0:
                return Response({"error": "Amount must be greater than zero."},
                                status=status.HTTP_400_BAD_REQUEST)

            total_balance = WalletTransactions.objects.filter(
                transaction_type='credit').aggregate(Sum('amount'))['amount__sum'] or 0
            if amount > total_balance:
                return Response({"error": "Insufficient balance."},
                                status=status.HTTP_400_BAD_REQUEST)

            WalletTransactions.objects.create(
                wallet_balance=-amount,
                amount=amount,
                transaction_type='debit'
            )
            return Response({"message": "Funds withdrawn successfully."},
                            status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WithdrawMoney(APIView):
    """
    View to handle withdrawal requests.
    Creates a new transaction and request for withdrawing funds from the wallet.
    """
    permission_classes = [IsAuthenticated, VerifiedUser]

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            amount = request.data.get('amount')
            upi_id = request.data.get('upi_id')

            if not amount or Decimal(amount) <= 0:
                return Response({"error": "Amount must be greater than zero."},
                                status=status.HTTP_400_BAD_REQUEST)

            latest_transaction = WalletTransactions.objects.filter(
                user=request.user).order_by('-created_at').first()
            latest_wallet_balance = latest_transaction.wallet_balance if latest_transaction else 0

            if latest_wallet_balance < Decimal(amount):
                return Response({"error": "Insufficient wallet balance."},
                                status=status.HTTP_400_BAD_REQUEST)

            uuid_for_payment = uuid.uuid4()

            try:
                payment_details = PaymentDetails.objects.create(
                    payment_method='upi',
                    transaction_id=str(uuid_for_payment),
                    payment_for='withdraw_to_wallet'
                )

                wallet_transaction_obj = WalletTransactions.objects.create(
                    user=request.user,
                    wallet_balance=latest_wallet_balance - Decimal(amount),
                    amount=Decimal(amount),
                    transaction_type='debit',
                    payment_details=payment_details
                )

                WithdrawingRequests.objects.create(
                    user=request.user, payment_obj=wallet_transaction_obj,
                    amount=Decimal(amount), upi_id=upi_id
                )

                return Response({"message": "Withdrawal requested successfully."},
                                status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawingRequestsViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing withdrawing requests.
    Allows partial updates to handle request status changes.
    """
    queryset = WithdrawingRequests.objects.all()
    serializer_class = WithdrawingRequestSerializer

    def get_queryset(self):
        status = self.request.query_params.get('status', None)
        if status:
            return self.queryset.filter(status=status)
        return self.queryset

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data

        if "status" in data:
            new_status = data['status']

            if new_status == 'success':
                self.handle_success_status(instance)

            elif new_status == 'rejected':
                self.handle_rejected_status(instance)

            else:
                return Response({"error": "Invalid status."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Status is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        return super().partial_update(request, *args, **kwargs)

    def handle_success_status(self, instance):
        """
        Handle successful withdrawal requests (to be implemented).
        """
        pass

    def handle_rejected_status(self, instance):
        """
        Handle rejected withdrawal requests by crediting the rejected amount back to the user's wallet.
        """
        latest_transaction = WalletTransactions.objects.filter(
            user=instance.user).order_by('-created_at').first()
        latest_wallet_balance = latest_transaction.wallet_balance if latest_transaction else 0
        WalletTransactions.objects.create(
            user=instance.user,
            payment_details=instance.payment_obj.payment_details,
            wallet_balance=(latest_wallet_balance + instance.amount),
            amount=instance.amount,
            transaction_type='credit'
        )


class WalletBalanceView(APIView):
    """
    View to get the current wallet balance.
    """
    permission_classes = [IsAuthenticated, VerifiedUser]

    def get(self, request, *args, **kwargs):
        try:
            latest_transaction = WalletTransactions.objects.filter(
                user=request.user).latest('created_at')
            total_balance = latest_transaction.wallet_balance
        except WalletTransactions.DoesNotExist:
            total_balance = 0

        return Response({"balance": total_balance}, status=status.HTTP_200_OK)



# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from .models import WalletTransactions, WithdrawingRequests, PaymentDetails
# from django.db.models import Sum
# from .serializers import WithdrawingRequestSerializer, WalletTransactionsSerializer, WalletDataSerializer
# from django.conf import settings
# import stripe
# from rest_framework.permissions import IsAuthenticated
# from server.permissions import VerifiedUser
# from django.templatetags.static import static
# import uuid
# from rest_framework import viewsets
# from decimal import Decimal
# from django.db import transaction


# class AddFundsView(APIView):
#     permission_classes = [IsAuthenticated, VerifiedUser]

#     def post(self, request, *args, **kwargs):

#         amount = int(request.data.get('amount'))
#         print(amount, 'amount')
#         if amount <= 0:
#             return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

#         image_url = request.build_absolute_uri(
#             static('images/add-to-wallet.png'))

#         session_price = (int(amount) * 100)
#         try:
#             checkout_session = stripe.checkout.Session.create(
#                 payment_method_types=['card'],
#                 line_items=[
#                     {
#                         'price_data': {
#                             'currency': 'inr',
#                             'product_data': {
#                                 'name': 'Add Money to Wallet',
#                                 'description':  f"Add money to the wallet by fullfilling the payment",
#                                 # 'images': [image_url],
#                             },
#                             'unit_amount': session_price,
#                         },
#                         'quantity': 1,
#                     },
#                 ],
#                 mode='payment',
#                 success_url=(settings.DOMAIN_URL + 'user/success' + '?checkout_id={CHECKOUT_SESSION_ID}') 
#                 if request.user.role == 'user' else (settings.DOMAIN_URL + 'lawyer/success' + '?checkout_id={CHECKOUT_SESSION_ID}'),
#                 # if request.user.role == 'user' else
#                 # (settings.DOMAIN_URL + 'lawyer/wallet/' + '?success={CHECKOUT_SESSION_ID}') if request.user.role == 'lawyer' else (
#                 #     settings.DOMAIN_URL + 'admin/wallet/' + '?success={CHECKOUT_SESSION_ID}'),
#                 cancel_url=(settings.DOMAIN_URL + 'user/fail/')
#                 if request.user.role == 'user' else
#                 (settings.DOMAIN_URL + 'lawyer/fail/'),
#                 metadata={
#                     'user_id': request.user.id,
#                     'payment_for': 'wallet',
#                 }
#             )

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         return Response({'sessionId': checkout_session.id}, status=status.HTTP_200_OK)


# class GetBalanceView(APIView):
#     permission_classes = [IsAuthenticated, VerifiedUser]

#     def get(self, request, *args, **kwargs):
#         try:
#             latest_transaction = WalletTransactions.objects.filter(
#                 user=request.user).latest('created_at')
#             total_balance = latest_transaction.wallet_balance
#         except WalletTransactions.DoesNotExist:
#             total_balance = 0
#         balance_history = WalletTransactions.objects.filter(
#             user=request.user).order_by('-created_at').all()
#         balance_data = WalletTransactionsSerializer(
#             balance_history, many=True).data
#         return Response({"balance": total_balance, 'balance_history': balance_data}, status=status.HTTP_200_OK)


# class WithdrawFundsView(APIView):
#     permission_classes = [IsAuthenticated, VerifiedUser]

#     def post(self, request, *args, **kwargs):
#         serializer = WalletDataSerializer(data=request.data)
#         if serializer.is_valid():
#             amount = serializer.validated_data.get('amount')
#             if amount <= 0:
#                 return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

#             total_balance = WalletTransactions.objects.filter(
#                 transaction_type='credit').aggregate(Sum('amount'))['amount__sum'] or 0
#             if amount > total_balance:
#                 return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

#             WalletTransactions.objects.create(
#                 wallet_balance=-amount,
#                 amount=amount,
#                 transaction_type='debit'
#             )
#             return Response({"message": "Funds withdrawn successfully."}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class WithdrawMoney(APIView):
#     permission_classes = [IsAuthenticated, VerifiedUser]

#     def post(self, request, *args, **kwargs):
#         with transaction.atomic():
#             amount = request.data.get('amount')
#             upi_id = request.data.get('upi_id')

#             if not amount or Decimal(amount) <= 0:
#                 return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

#             latest_transaction = WalletTransactions.objects.filter(
#                 user=request.user).order_by('-created_at').first()
#             latest_wallet_balance = latest_transaction.wallet_balance if latest_transaction else 0

#             if latest_wallet_balance < Decimal(amount):
#                 return Response({"error": "Insufficient wallet balance."}, status=status.HTTP_400_BAD_REQUEST)

#             uuid_for_payment = uuid.uuid4()

#             try:
#                 payment_details = PaymentDetails.objects.create(
#                     payment_method='upi',
#                     transaction_id=str(uuid_for_payment),
#                     payment_for='withdraw_to_wallet'
#                 )

#                 wallet_transaction_obj = WalletTransactions.objects.create(
#                     user=request.user,
#                     wallet_balance=latest_wallet_balance - Decimal(amount),
#                     amount=Decimal(amount),
#                     transaction_type='debit',
#                     payment_details=payment_details
#                 )

#                 WithdrawingRequests.objects.create(
#                     user=request.user, payment_obj=wallet_transaction_obj, amount=Decimal(amount), upi_id=upi_id)

#                 return Response({"message": "Withdrawal requested successfully."}, status=status.HTTP_200_OK)

#             except Exception as e:
#                 return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class WithdrawingRequestsViewSet(viewsets.ModelViewSet):
#     queryset = WithdrawingRequests.objects.all()
#     serializer_class = WithdrawingRequestSerializer

#     def get_queryset(self):
#         status = self.request.query_params.get('status', None)
#         if status:
#             return self.queryset.filter(status=status)
#         return self.queryset

#     def partial_update(self, request, *args, **kwargs):
#         instance = self.get_object()

#         data = request.data

#         if "status" in data:
#             new_status = data['status']

#             if new_status == 'success':
#                 self.handle_success_status(instance)

#             elif new_status == 'rejected':
#                 self.handle_rejected_status(instance)

#             else:
#                 return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({"error": "Status is required."}, status=status.HTTP_400_BAD_REQUEST)

#         return super().partial_update(request, *args, **kwargs)

#     def handle_success_status(self, instance):
#         pass

#     def handle_rejected_status(self, instance):
#         latest_transaction = WalletTransactions.objects.filter(
#             user=instance.user).order_by('-created_at').first()
#         latest_wallet_balance = latest_transaction.wallet_balance if latest_transaction else 0
#         WalletTransactions.objects.create(user=instance.user, payment_details=instance.payment_obj.payment_details, wallet_balance=(
#             latest_wallet_balance + instance.amount), amount=instance.amount, transaction_type='credit')


# class WalletBalanceView(APIView):
#     permission_classes = [IsAuthenticated, VerifiedUser]

#     def get(self, request, *args, **kwargs):
#         try:
#             latest_transaction = WalletTransactions.objects.filter(
#                 user=request.user).latest('created_at')
#             total_balance = latest_transaction.wallet_balance
#         except WalletTransactions.DoesNotExist:
#             total_balance = 0

#         return Response({"balance": total_balance}, status=status.HTTP_200_OK)
