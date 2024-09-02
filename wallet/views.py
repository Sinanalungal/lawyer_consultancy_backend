from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import WalletTransactions
from django.db.models import Sum
from .serializers import WalletTransactionsSerializer,WalletDataSerializer
from django.conf import settings
import stripe

# class BookAppointmentView(APIView):
#     """
#     API view to create a Stripe checkout session for booking an appointment.
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         try:
#             scheduling_uuid = request.data.get('scheduling_uuid')
#             scheduling_date_str = request.data.get('scheduling_date')
#             print(scheduling_date_str,scheduling_uuid)

#             if not scheduling_uuid or not scheduling_date_str:
#                 print('Missing scheduling UUID or date')
#                 return Response({'error': 'Scheduling UUID and date are required.'}, status=status.HTTP_400_BAD_REQUEST)

#             # Parse scheduling_date_str into a date object
#             try:
#                 scheduling_date = datetime.strptime(
#                     scheduling_date_str, '%Y-%m-%d').date()
#             except ValueError:
#                 print('invalid date format')
#                 return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

#             # Fetch the Scheduling object using the UUID
#             scheduling = get_object_or_404(Scheduling, pk=scheduling_uuid)

#             # Combine the scheduling date and start time
#             session_date = datetime.combine(
#                 scheduling_date, scheduling.start_time)

#             # Check if the scheduling is available
#             if BookedAppointment.objects.filter(scheduling=scheduling).exists():
#                 print('session is not available now')
#                 return Response({'error': 'Session is not available now.'}, status=status.HTTP_400_BAD_REQUEST)
            
#             # Create a Stripe Checkout Session
#             session_price = int(scheduling.price * 100)
#             try:
#                 checkout_session = stripe.checkout.Session.create(
#                     payment_method_types=['card'],
#                     line_items=[
#                         {
#                             'price_data': {
#                                 'currency': 'inr',
#                                 'product_data': {
#                                     'name': f"{scheduling.lawyer_profile.user.full_name}'s Session Appointment",
#                                 },
#                                 'unit_amount': session_price,
#                             },
#                             'quantity': 1,
#                         },
#                     ],
#                     mode='payment',
#                     success_url=settings.DOMAIN_URL + 'user/available-sessions/'+'?success={CHECKOUT_SESSION_ID}',
#                     cancel_url=settings.DOMAIN_URL + 'cancel',
#                     metadata={
#                         'scheduling_uuid': scheduling_uuid,
#                         'scheduling_date': scheduling_date_str,
#                         'user_id': request.user.id,
#                         'payment_for':'session',
#                     }
#                 )
#                 return Response({'sessionId': checkout_session.id}, status=status.HTTP_201_CREATED)
#             except Exception as e:
#                 print('error with session saving')
#                 return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddFundsView(APIView):
    def post(self, request, *args, **kwargs):
        # serializer = WalletTransactionsSerializer(data=request.data)
        # if serializer.is_valid():
        amount = int(request.data.get('amount'))
        print(amount, 'amount')
        if amount <= 0:
            return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        # WalletTransactions.objects.create(
        #     wallet_balance=amount,
        #     amount=amount,
        #     transaction_type='credit'
        # )
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
            success_url=(settings.DOMAIN_URL + 'user/available-sessions/' + '?success={CHECKOUT_SESSION_ID}')
                        if request.user.role == 'user' else 
                        (settings.DOMAIN_URL + 'other-path/' + '?success={CHECKOUT_SESSION_ID}'),
            cancel_url=settings.DOMAIN_URL + 'cancel',
            metadata={
                'user_id': request.user.id,
                'payment_for': 'wallet',
            }
        )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'sessionId':checkout_session.id}, status=status.HTTP_200_OK)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetBalanceView(APIView):

    def get(self, request, *args, **kwargs):
        total_balance = WalletTransactions.objects.latest('created_at').wallet_balance
        balance_history = WalletTransactions.objects.filter(user=request.user).all()
        balance_data = WalletTransactionsSerializer(balance_history, many=True).data
        return Response({"balance": total_balance, 'balance_history': balance_data}, status=status.HTTP_200_OK)
    
    
class WithdrawFundsView(APIView):
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