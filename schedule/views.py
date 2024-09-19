from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from server.permissions import IsLawyer, IsAdmin,VerifiedUser
from django.core.exceptions import ValidationError
from .models import Scheduling, BookedAppointment, PaymentDetails
from .serializers import (
    SchedulingSerializer,
    BookedAppointmentSerializerForSalesReport,
    BookedAppointmentSerializer,
    ScheduledSerializer,
    SheduledSerilizerForUserSide,
    SchedulingSerializerForAdmin,
)
from api.models import LawyerProfile
from rest_framework.views import APIView
from django.utils.dateparse import parse_date
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db import transaction
import stripe
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from wallet.models import WalletTransactions
from django.utils import timezone
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter


class SchedulingCreateView(generics.CreateAPIView):
    queryset = Scheduling.objects.all()
    serializer_class = SchedulingSerializer
    permission_classes = [IsLawyer,VerifiedUser]

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
    permission_classes = [IsLawyer,VerifiedUser]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user.email
        return Scheduling.objects.filter(lawyer_profile__user__email=user, is_listed=True, is_canceled=False)


class ActiveSchedulesView(generics.ListAPIView):
    serializer_class = SheduledSerilizerForUserSide
    permission_classes = [IsLawyer,VerifiedUser]

    def get_queryset(self):
        user = self.request.user.email
        return Scheduling.objects.filter(lawyer_profile__user__email=user, is_listed=True, is_canceled=False)


class CancelScheduleView(generics.UpdateAPIView):
    permission_classes = [IsLawyer,VerifiedUser]
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
    permission_classes=[IsAuthenticated,VerifiedUser]
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

        now_time = now.time()

        if date < today:
            print('Date<today is working')
            return Response({"times": []})

        try:
            if date == today:
                scheduling_queryset = Scheduling.objects.filter(
                    lawyer_profile__pk=lawyer_id,
                    date__lte=date,
                    is_listed=True,
                    is_canceled=False,
                    reference_until__gte=date,
                    start_time__gt=now_time
                ).order_by('start_time')
            else:
                scheduling_queryset = Scheduling.objects.filter(
                    lawyer_profile__pk=lawyer_id,
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
    permission_classes = [IsAuthenticated,VerifiedUser]

    def post(self, request, *args, **kwargs):
        try:
            scheduling_uuid = request.data.get('scheduling_uuid')
            scheduling_date_str = request.data.get('scheduling_date')
            print(scheduling_date_str, scheduling_uuid)

            if not scheduling_uuid or not scheduling_date_str:
                print('Missing scheduling UUID or date')
                return Response({'error': 'Scheduling UUID and date are required.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                scheduling_date = datetime.strptime(
                    scheduling_date_str, '%Y-%m-%d').date()
            except ValueError:
                print('invalid date format')
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

            scheduling = get_object_or_404(Scheduling, pk=scheduling_uuid)

            session_date = datetime.combine(
                scheduling_date, scheduling.start_time)

            if BookedAppointment.objects.filter(scheduling=scheduling).exists():
                print('session is not available now')
                return Response({'error': 'Session is not available now.'}, status=status.HTTP_400_BAD_REQUEST)

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
                    success_url=settings.DOMAIN_URL + 'user/available-sessions/' +
                    '?success={CHECKOUT_SESSION_ID}',
                    cancel_url=settings.DOMAIN_URL + f"user/available-sessions/?cancel=true",
                    metadata={
                        'scheduling_uuid': scheduling_uuid,
                        'scheduling_date': scheduling_date_str,
                        'user_id': request.user.id,
                        'payment_for': 'session',
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

        session = event['data']['object']
        if event['type'] == 'checkout.session.completed' and session['metadata']['payment_for'] == 'session':
            scheduling_uuid = session['metadata']['scheduling_uuid']
            scheduling_date_str = session['metadata']['scheduling_date']
            user_id = session['metadata']['user_id']
            print('working')
            try:
                with transaction.atomic():
                    scheduling = Scheduling.objects.get(pk=scheduling_uuid)
                    scheduling_date = datetime.strptime(
                        scheduling_date_str, '%Y-%m-%d').date()
                    lawyer_obj = scheduling.lawyer_profile.user
                    payment_details = PaymentDetails.objects.create(
                        payment_method=session['payment_method_types'][0],
                        transaction_id=session['payment_intent'],
                        payment_for='session'
                    )

                    obj = BookedAppointment.objects.create(
                        scheduling=scheduling,
                        user_profile_id=user_id,
                        session_date=datetime.combine(
                            scheduling_date, scheduling.start_time),
                        payment_details=payment_details,
                        is_transaction_completed=True,
                    )

                    try:
                        latest_transaction = WalletTransactions.objects.filter(
                            user=lawyer_obj).latest('created_at')
                        print(latest_transaction)
                        latest_wallet_balance = latest_transaction.wallet_balance
                    except:
                        latest_wallet_balance = 0

                    price_for_lawyer = (float(scheduling.price)*0.9)
                    latest_wallet_balance = float(
                        latest_wallet_balance)+price_for_lawyer
                    WalletTransactions.objects.create(user=lawyer_obj, payment_details=payment_details,
                                                      wallet_balance=latest_wallet_balance, amount=price_for_lawyer, transaction_type='credit')

                    scheduling.is_listed = False
                    scheduling.save()

            except Scheduling.DoesNotExist:
                print('Scheduling does not exist')
                return JsonResponse({'error': 'Scheduling not found'}, status=400)
            except Exception as e:
                print('Error occurred:', str(e))
                return JsonResponse({'error': str(e)}, status=500)
        elif event['type'] == 'checkout.session.completed' and session['metadata']['payment_for'] == 'wallet':
            print('getting to the wallet working part....')
            user_id = session['metadata']['user_id']
            try:
                with transaction.atomic():
                    payment_details = PaymentDetails.objects.create(
                        payment_method=session['payment_method_types'][0],
                        transaction_id=session['payment_intent'],
                        payment_for='wallet'
                    )

                    try:
                        latest_transaction = WalletTransactions.objects.filter(
                            user=lawyer_obj).latest('created_at')
                        print(latest_transaction)
                        latest_wallet_balance = latest_transaction.wallet_balance
                    except:
                        latest_wallet_balance = 0

                    print(latest_wallet_balance)
                    print(session)
                    price = float(session['amount_subtotal'])/100
                    print(price)
                    obj = WalletTransactions.objects.create(
                        wallet_balance=float(latest_wallet_balance)+price,
                        amount=price,
                        transaction_type='credit',
                        user_id=int(user_id),
                        payment_details=payment_details
                    )
                    print(obj)

            except Exception as e:
                print('Error occurred:', str(e))
                return JsonResponse({'error': str(e)}, status=500)
        return JsonResponse({'status': 'success'}, status=200)


class BookedAppointmentsListView(generics.ListAPIView):
    serializer_class = BookedAppointmentSerializer
    permission_classes = [IsAuthenticated,VerifiedUser]

    def get_queryset(self):
        query_param = self.request.query_params.get('type')
        now = timezone.now()
        user = self.request.user
        print(query_param)
        if user.role == 'lawyer':
            lawyer_profile = user.lawyer_profile
            if query_param == 'upcoming':
                print('getting in to the lawyer upcoming')
                return BookedAppointment.objects.filter(
                    scheduling__lawyer_profile=lawyer_profile,
                    is_transaction_completed=True,
                    is_completed=False,
                    is_canceled=False,
                ).filter(
                    Q(session_date__date__gt=now.date()) |
                    (Q(session_date__date=now.date()) & Q(
                        scheduling__end_time__gte=now.time()))
                ).select_related('scheduling__lawyer_profile')
            elif query_param == 'completed':
                print('getting in to the lawyer finished')
                return BookedAppointment.objects.filter(
                    scheduling__lawyer_profile=lawyer_profile,
                    is_transaction_completed=True,
                    is_canceled=False,
                ).filter(
                    Q(session_date__date__lt=now.date()) |
                    (Q(session_date__date=now.date()) & Q(
                        scheduling__end_time__lt=now.time()))
                ).select_related('scheduling__lawyer_profile')

        elif user.role == 'user':
            if query_param == 'upcoming':
                print('getting in to the user upcoming')
                return BookedAppointment.objects.filter(
                    user_profile=user,
                    is_transaction_completed=True,
                    is_completed=False,
                    is_canceled=False,
                ).filter(
                    Q(session_date__date__gt=now.date()) |
                    (Q(session_date__date=now.date()) & Q(
                        scheduling__end_time__gte=now.time()))
                ).select_related('scheduling__lawyer_profile')
            elif query_param == 'finished':
                print('getting in to the user finished')
                return BookedAppointment.objects.filter(
                    user_profile=user,
                    is_transaction_completed=True,
                    is_canceled=False,
                ).filter(
                    Q(session_date__date__lt=now.date()) |
                    (Q(session_date__date=now.date()) & Q(
                        scheduling__end_time__lt=now.time()))
                ).select_related('scheduling__lawyer_profile')

        return BookedAppointment.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        print(serializer.data)
        return Response(serializer.data)


class SchedulingListViewForAdmin(generics.ListAPIView):
    serializer_class = SchedulingSerializerForAdmin
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    permission_classes = [IsAdmin,VerifiedUser]
    search_fields = ['date', 'start_time', 'end_time',
                     'price', 'lawyer_profile__user__full_name']

    def get_queryset(self):
        queryset = Scheduling.objects.filter(is_canceled=False)
        is_listed_param = self.request.query_params.get('is_listed', None)

        if is_listed_param is not None:
            queryset = queryset.filter(is_listed=is_listed_param == 'true')

        return queryset


class SchedulingUpdateViewAdmin(generics.UpdateAPIView):
    queryset = Scheduling.objects.all()
    serializer_class = SchedulingSerializerForAdmin
    permission_classes = [IsAdmin,VerifiedUser]

    def patch(self, request, *args, **kwargs):
        scheduling_id = kwargs.get('pk')
        is_listed = request.data.get('is_listed', None)

        if is_listed is not None:
            try:
                scheduling = self.get_object()
                scheduling.is_listed = is_listed
                scheduling.save()
                serializer = self.get_serializer(scheduling)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Scheduling.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "Bad request."}, status=status.HTTP_400_BAD_REQUEST)


class SuccessFullSessionReportView(generics.ListAPIView):
    serializer_class = BookedAppointmentSerializerForSalesReport
    permission_classes = [IsAdmin,VerifiedUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user_profile__full_name',
                     'scheduling__lawyer_profile__user__full_name']

    def get_queryset(self):
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        search = self.request.query_params.get('search', None)

        qs = BookedAppointment.objects.filter(
            Q(is_canceled=False) & Q(is_completed=True)
        )

        if from_date:
            try:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                qs = qs.filter(booked_at__gte=from_date)
            except ValueError:
                raise ValidationError(
                    'Invalid from_date format, expected YYYY-MM-DD.')

        if to_date:
            try:
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                qs = qs.filter(booked_at__lte=to_date)
            except ValueError:
                raise ValidationError(
                    'Invalid to_date format, expected YYYY-MM-DD.')

        if search:
            qs = qs.filter(Q(user_profile__full_name__icontains=search) |
                           Q(scheduling__lawyer_profile__user__full_name__icontains=search))

        return qs.select_related('payment_details', 'scheduling__lawyer_profile__user', 'user_profile')


class ForDownloadDataFetching(generics.ListAPIView):
    serializer_class = BookedAppointmentSerializerForSalesReport
    permission_classes = [IsAdmin,VerifiedUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user_profile__full_name',
                     'scheduling__lawyer_profile__user__full_name']
    pagination_class = None

    def get_queryset(self):
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        search = self.request.query_params.get('search', None)

        qs = BookedAppointment.objects.filter(
            Q(is_canceled=False) & Q(is_completed=True)
        )

        if from_date:
            try:
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                qs = qs.filter(booked_at__gte=from_date)
            except ValueError:
                raise ValidationError(
                    'Invalid from_date format, expected YYYY-MM-DD.')

        if to_date:
            try:
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                qs = qs.filter(booked_at__lte=to_date)
            except ValueError:
                raise ValidationError(
                    'Invalid to_date format, expected YYYY-MM-DD.')

        if search:
            qs = qs.filter(Q(user_profile__full_name__icontains=search) |
                           Q(scheduling__lawyer_profile__user__full_name__icontains=search))

        return qs.select_related('payment_details', 'scheduling__lawyer_profile__user', 'user_profile')
