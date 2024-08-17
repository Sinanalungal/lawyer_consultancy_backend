from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from server.permissions import IsLawyer
from django.core.exceptions import ValidationError
from .models import Scheduling, BookedAppointment,PaymentDetails
from .serializers import SchedulingSerializer,BookedAppointmentSerializer, ScheduledSerializer, SheduledSerilizerForUserSide
from api.models import LawyerProfile
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from django.utils.dateparse import parse_date
# from django.utils import timezone
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.db import transaction
import stripe
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class SchedulingCreateView(generics.CreateAPIView):
    queryset = Scheduling.objects.all()
    serializer_class = SchedulingSerializer
    permission_classes = [IsLawyer]

    def perform_create(self, serializer):
        user_email = self.request.user.email
        print(user_email)
        try:
            lawyer_profile = LawyerProfile.objects.get(user__email=user_email)
        except LawyerProfile.DoesNotExist:
            raise ValidationError(
                "No LawyerProfile associated with the current user.")
        serializer.save(lawyer_profile=lawyer_profile)

    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UserSessionsView(generics.ListAPIView):
    serializer_class = ScheduledSerializer
    permission_classes = [IsLawyer]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user.email
        return Scheduling.objects.filter(lawyer_profile__user__email=user, is_listed=True, is_canceled=False)


# from rest_framework.pagination import PageNumberPagination

# class CustomPagination(PageNumberPagination):
#     page_size = 2

class ActiveSchedulesView(generics.ListAPIView):
    serializer_class = SheduledSerilizerForUserSide
    permission_classes = [IsLawyer]
    # pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user.email
        return Scheduling.objects.filter(lawyer_profile__user__email=user, is_listed=True, is_canceled=False)


class CancelScheduleView(generics.UpdateAPIView):
    permission_classes = [IsLawyer]
    queryset = Scheduling.objects.all()
    lookup_field = 'uuid'

    def update(self, request, *args, **kwargs):
        schedule = self.get_object()
        if schedule.is_canceled:
            return Response({'detail': 'This schedule is already canceled.'}, status=status.HTTP_400_BAD_REQUEST)

        schedule.is_canceled = True
        schedule.save()
        return Response({'detail': 'Schedule canceled successfully.'}, status=status.HTTP_200_OK)


class AvailableSlotsView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        date_str = request.query_params.get('date')
        lawyer_id = request.query_params.get('lawyer_id')
        print(f'date_str: {date_str}, lawyer_id: {lawyer_id}')

        if not date_str or not lawyer_id:
            print('Invalid parameters')
            return Response({"detail": "Date and lawyer_id parameters are required."}, status=400)

        date = parse_date(date_str)
        if not date:
            print('Invalid date format')
            return Response({"detail": "Invalid date format."}, status=400)

        now = datetime.now() 
        today = datetime.today().date()  

        # Convert current time to time object
        now_time = now.time()

        # If the requested date is in the past, return an empty queryset
        if date < today:
            print('Date<today is working')
            return Response({"times": []})

        try:
            if date == today:
                scheduling_queryset = Scheduling.objects.filter(
                    pk=lawyer_id,
                    date__lte=date,
                    is_listed=True,
                    is_canceled=False,
                    reference_until__gte=date,
                    start_time__gt=now_time
                ).order_by('start_time')
            else:
                scheduling_queryset = Scheduling.objects.filter(
                    pk=lawyer_id,
                    date__lte=date,
                    is_listed=True,
                    is_canceled=False,
                    reference_until__gte=date,
                ).order_by('start_time')
            print(scheduling_queryset)
            available_times = []
            for scheduling in scheduling_queryset:
                available_times.append({
                    'uuid': scheduling.pk,
                    "start_time": scheduling.start_time.strftime("%I:%M %p"),
                    "end_time": scheduling.end_time.strftime("%I:%M %p"),
                    "price": str(scheduling.price)
                })

            return Response({"times": available_times})
        except Scheduling.DoesNotExist:
            print('scheduling doesnot exist works')
            return Response({"times": []})



stripe.api_key = settings.STRIPE_API_KEY

class BookAppointmentView(APIView):
    """
    API view to create a Stripe checkout session for booking an appointment.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            scheduling_uuid = request.data.get('scheduling_uuid')
            scheduling_date_str = request.data.get('scheduling_date')
            print(scheduling_date_str,scheduling_uuid)

            if not scheduling_uuid or not scheduling_date_str:
                print('Missing scheduling UUID or date')
                return Response({'error': 'Scheduling UUID and date are required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Parse scheduling_date_str into a date object
            try:
                scheduling_date = datetime.strptime(
                    scheduling_date_str, '%Y-%m-%d').date()
            except ValueError:
                print('invalid date format')
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the Scheduling object using the UUID
            scheduling = get_object_or_404(Scheduling, pk=scheduling_uuid)

            # Combine the scheduling date and start time
            session_date = datetime.combine(
                scheduling_date, scheduling.start_time)

            # Check if the scheduling is available
            if BookedAppointment.objects.filter(scheduling=scheduling).exists():
                print('session is not available now')
                return Response({'error': 'Session is not available now.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create a Stripe Checkout Session
            session_price = int(scheduling.price * 100)
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'inr',
                                'product_data': {
                                    'name': f"{scheduling.lawyer_profile.user.full_name}'s Session Appointment",
                                },
                                'unit_amount': session_price,
                            },
                            'quantity': 1,
                        },
                    ],
                    mode='payment',
                    success_url=settings.DOMAIN_URL + 'user/available-sessions/'+'?success={CHECKOUT_SESSION_ID}',
                    cancel_url=settings.DOMAIN_URL + 'cancel',
                    metadata={
                        'scheduling_uuid': scheduling_uuid,
                        'scheduling_date': scheduling_date_str,
                        'user_id': request.user.id,
                    }
                )
                return Response({'sessionId': checkout_session.id}, status=status.HTTP_201_CREATED)
            except Exception as e:
                print('error with session saving')
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    endpoint_secret = 'whsec_e883094ce98575db46ef700f91d94786f4b4cec88e05d6c7c3cc7c753e5543cd'
    # settings.STRIPE_WEBHOOK_SECRET

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        print('entering')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.endpoint_secret
            )
            print(event)
        except ValueError:
            print('Invalid payload')
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            print('Invalid signature')
            return JsonResponse({'error': 'Invalid signature'}, status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            scheduling_uuid = session['metadata']['scheduling_uuid']
            scheduling_date_str = session['metadata']['scheduling_date']
            user_id = session['metadata']['user_id']
            print('working')
            try:
                with transaction.atomic():
                    scheduling = Scheduling.objects.get(pk=scheduling_uuid)
                    scheduling_date = datetime.strptime(scheduling_date_str, '%Y-%m-%d').date()

                    payment_details = PaymentDetails.objects.create(
                        payment_method=session['payment_method_types'][0],
                        transaction_id=session['payment_intent'],
                    )
                    
                    # Create the booked appointment
                    obj=BookedAppointment.objects.create(
                        scheduling=scheduling,
                        user_profile_id=user_id,
                        session_date=datetime.combine(scheduling_date, scheduling.start_time),
                        payment_details=payment_details,
                        is_transaction_completed=True,
                    )
                    scheduling.is_listed = False
                    scheduling.save()

            except Scheduling.DoesNotExist:
                print('Scheduling does not exist')
                return JsonResponse({'error': 'Scheduling not found'}, status=400)
            except Exception as e:
                print('Error occurred:', str(e))
                return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'status': 'success'}, status=200)

# class CheckoutSession(APIView):
#     def post(self, request, *args, **kwargs):
#         print('entering into checkout')
#         subscription_id = request.data.get('subscription_id')
#         lawyer_id = request.data.get('lawyer_id')
#         user_id = request.data.get('user_id')
#         print(lawyer_id)
        
#         subscription = SubscriptionPlan.objects.filter(id=subscription_id, valid=True).first()
#         subscription_name = subscription.plan.name
#         subscription_price = int(subscription.price * 100)  # Price in paise (e.g., ₹20.00)

#         try:
#             # Create a checkout session with price data and metadata
#             checkout_session = stripe.checkout.Session.create(
#                 payment_method_types=['card'],
#                 line_items=[
#                     {
#                         'price_data': {
#                             'currency': 'inr',
#                             'product_data': {
#                                 'name': subscription_name,
#                             },
#                             'unit_amount': subscription_price,
#                         },
#                         'quantity': 1,
#                     },
#                 ],
#                 mode='payment',
#                 success_url=settings.DOMAIN_URL + 'user?success=true&session_id={CHECKOUT_SESSION_ID}',
#                 cancel_url=settings.DOMAIN_URL + f'user/subscription/{lawyer_id}?canceled=true',
#                 metadata={
#                     'subscription_id': subscription_id,
#                     'user_id': user_id,
#                 }
#             )
#             print('success')
#         except Exception as e:
#             print('failed')
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         print(checkout_session.id)
#         return Response(checkout_session.id, status=status.HTTP_200_OK)
    


class BookedAppointmentsListView(generics.ListAPIView):
    serializer_class = BookedAppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query_param = self.request.query_params.get('type')
        
        if query_param == 'upcoming':
            return BookedAppointment.objects.filter(
                user_profile=self.request.user,
                is_transaction_completed=True,
                is_completed=False,
                is_canceled=False
            ).select_related('scheduling__lawyer_profile')
        elif query_param == 'finished':
            return BookedAppointment.objects.filter(
                user_profile=self.request.user,
                is_transaction_completed=True,
                is_completed=True,
                is_canceled=False
            ).select_related('scheduling__lawyer_profile')
        else:
            return BookedAppointment.objects.none() 

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
