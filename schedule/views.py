from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from server.permissions import IsLawyer, IsAdmin, VerifiedUser, ObjectBasedUsers
from django.core.exceptions import ValidationError
from .models import Scheduling, BookedAppointment, PaymentDetails, CeleryTasks
from .serializers import (
    SchedulingSerializer,
    BookedAppointmentSerializerForSalesReport,
    BookedAppointmentSerializer,
    ScheduledSerializer,
    SheduledSerilizerForUserSide,
    SchedulingSerializerForAdmin,
)
from datetime import timedelta
from api.models import LawyerProfile
from notifications.models import Notifications
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
from decimal import Decimal
from django.templatetags.static import static
from django.urls import reverse
import uuid
from notifications.tasks import send_money_to_the_lawyer_wallet
from django.shortcuts import get_object_or_404
from celery import current_app


stripe.api_key = settings.STRIPE_API_KEY


class SchedulingCreateView(generics.CreateAPIView):
    queryset = Scheduling.objects.all()
    serializer_class = SchedulingSerializer
    permission_classes = [IsLawyer, VerifiedUser]

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
        try:
            print(request.data)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            return Response({"detail": e}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            try:
                error_details = e.detail
            except:
                error_details = str(e)

        # If there are non-field errors, extract them specifically
            if 'non_field_errors' in error_details:
                return Response(
                    {"detail": error_details['non_field_errors']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(error_details, status=status.HTTP_400_BAD_REQUEST)
        # Otherwise, return the whole error object


class UserSessionsView(generics.ListAPIView):
    serializer_class = ScheduledSerializer
    permission_classes = [IsLawyer, VerifiedUser]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        date_time = timezone.now()
        date = date_time.date()
        time = date_time.time()
        return Scheduling.objects.filter(lawyer_profile__user=user, date__gte=date, start_time__gt=time, is_listed=True, is_canceled=False)


class ActiveSchedulesView(generics.ListAPIView):
    serializer_class = SheduledSerilizerForUserSide
    permission_classes = [IsLawyer, VerifiedUser]

    def get_queryset(self):
        user = self.request.user.email
        return Scheduling.objects.filter(lawyer_profile__user__email=user, is_listed=True, is_canceled=False)


class AvailableSlotsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, VerifiedUser]

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
                print('date is today')
                scheduling_queryset = Scheduling.objects.filter(
                    lawyer_profile__pk=lawyer_id,
                    date=date,
                    is_listed=True,
                    is_canceled=False,
                    # reference_until__gte=date,
                    start_time__gt=now_time
                ).order_by('start_time')
            else:
                print('date is not today')
                scheduling_queryset = Scheduling.objects.filter(
                    lawyer_profile__pk=lawyer_id,
                    date=date,
                    is_listed=True,
                    is_canceled=False,
                    # reference_until__gte=date,
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


class BookAppointmentView(APIView):
    """
    API view to create a Stripe checkout session for booking an appointment.
    """
    permission_classes = [IsAuthenticated, VerifiedUser]

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

            # session_date = datetime.combine(
            #     scheduling_date, scheduling.start_time)

            if not scheduling.is_listed or scheduling.is_canceled:
                print('session is not available now')
                return Response({'error': 'Session is not available now.'}, status=status.HTTP_400_BAD_REQUEST)

            # if BookedAppointment.objects.filter(scheduling=scheduling).exists():
            #     print('session is not available now')
            #     return Response({'error': 'Session is not available now.'}, status=status.HTTP_400_BAD_REQUEST)

            session_price = int(scheduling.price * 100)
            image_url = request.build_absolute_uri(
                static('images/appointment.png'))
            print(image_url)
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'inr',
                                'product_data': {
                                    'name': 'Appointment Schedule',
                                    'description':  f"{scheduling.lawyer_profile.user.full_name}'s session appointment",
                                    # 'images': [image_url],
                                },
                                'unit_amount': session_price,
                            },
                            'quantity': 1,
                        },
                    ],
                    mode='payment',
                    success_url=settings.DOMAIN_URL + 'user/available-sessions/success' + \
                    '?checkout_id={CHECKOUT_SESSION_ID}',
                    cancel_url=settings.DOMAIN_URL + 'user/available-sessions/fail',
                    metadata={
                        'scheduling_uuid': scheduling_uuid,
                        'scheduling_date': scheduling_date_str,
                        'user_id': request.user.id,
                        'payment_for': 'session-using-card',
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
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        print('entering')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.endpoint_secret
            )
            print(event)
            session = event['data']['object']

            if event['type'] == 'checkout.session.completed':
                if session['metadata']['payment_for'] == 'session-using-card':
                    return self.handle_session_payment(session)
                elif session['metadata']['payment_for'] == 'wallet':
                    return self.handle_wallet_payment(session)
                elif session['metadata']['payment_for'] == 'session-using-card-wallet':
                    return self.handle_session_using_wallet_card_payment(session)

            return JsonResponse({'status': 'success'}, status=200)
        except ValueError:
            print('Invalid payload')
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            print('Invalid signature')
            return JsonResponse({'error': 'Invalid signature'}, status=400)

    def handle_session_payment(self, session):
        scheduling_uuid = session['metadata']['scheduling_uuid']
        scheduling_date_str = session['metadata']['scheduling_date']
        user_id = session['metadata']['user_id']
        print('working')

        try:
            with transaction.atomic():
                scheduling = Scheduling.objects.select_for_update().get(pk=scheduling_uuid)
                scheduling_date = datetime.strptime(
                    scheduling_date_str, '%Y-%m-%d').date()

                payment_details = PaymentDetails.objects.create(
                    payment_method=session['payment_method_types'][0],
                    transaction_id=session['payment_intent'],
                    payment_for='session'
                )

                appointment_obj = BookedAppointment.objects.create(
                    scheduling=scheduling,
                    user_profile_id=user_id,
                    session_start=datetime.combine(
                        scheduling_date, scheduling.start_time),
                    session_end=datetime.combine(
                        scheduling_date, scheduling.end_time),
                    # session_date=datetime.combine(scheduling_date, scheduling.start_time),
                    payment_details=payment_details,
                    # is_transaction_completed=True,
                )
                session_start_time = timezone.make_aware(
                    datetime.combine(scheduling_date, scheduling.start_time))
                print(session_start_time)
                naive_datetime = datetime.now()
                aware_datetime = timezone.make_aware(
                    naive_datetime, timezone.get_current_timezone())
                Notifications.objects.create(user_id=scheduling.lawyer_profile.user.pk, title='User booked an appointment',
                                             description=f"session id:{appointment_obj.uuid} scheduled for time:{appointment_obj.session_start}", notify_time=aware_datetime)
                Notifications.objects.create(user_id=user_id, title='Session will Starts Now',
                                             description=f"Appoinment id:{appointment_obj.uuid} session will starts now", notify_time=session_start_time)
                Notifications.objects.create(user_id=scheduling.lawyer_profile.user.pk, title='Session will Starts Now',
                                             description=f"Appoinment id:{appointment_obj.uuid} session will starts now", notify_time=session_start_time)

                scheduling.is_listed = False
                scheduling.save()
                session_end_time = timezone.make_aware(
                    appointment_obj.session_end)
                print((session_end_time - timedelta(minutes=5)),
                      'this is the celery task scheduled time')
                celery_task_obj = send_money_to_the_lawyer_wallet.apply_async(
                    args=[scheduling.lawyer_profile.user.pk,
                          payment_details.pk, appointment_obj.pk],
                    eta=(session_end_time - timedelta(minutes=5))
                )
                CeleryTasks.objects.create(
                    appointment=appointment_obj, task_id=celery_task_obj.id)
        except Scheduling.DoesNotExist:
            print('Scheduling does not exist')
            return JsonResponse({'error': 'Scheduling not found'}, status=400)
        except Exception as e:
            print('Error occurred:', str(e))
            return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'status': 'success'}, status=200)

    def handle_session_using_wallet_card_payment(self, session):
        scheduling_uuid = session['metadata']['scheduling_uuid']
        scheduling_date_str = session['metadata']['scheduling_date']
        user_id = session['metadata']['user_id']
        print('working')

        try:
            with transaction.atomic():
                scheduling = Scheduling.objects.select_for_update().get(pk=scheduling_uuid)
                scheduling_date = datetime.strptime(
                    scheduling_date_str, '%Y-%m-%d').date()

                payment_details = PaymentDetails.objects.create(
                    payment_method=session['payment_method_types'][0],
                    transaction_id=session['payment_intent'],
                    payment_for='session'
                )

                appointment_obj = BookedAppointment.objects.create(
                    scheduling=scheduling,
                    user_profile_id=user_id,
                    session_start=datetime.combine(
                        scheduling_date, scheduling.start_time),
                    session_end=datetime.combine(
                        scheduling_date, scheduling.end_time),
                    # session_date=datetime.combine(scheduling_date, scheduling.start_time),
                    payment_details=payment_details,
                    # is_transaction_completed=True,
                )

                latest_transaction = WalletTransactions.objects.filter(
                    user_id=user_id).order_by('-created_at').first()

                latest_wallet_balance = latest_transaction.wallet_balance if latest_transaction else 0

                if latest_wallet_balance != 0:
                    used_amount_from_wallet = Decimal(latest_wallet_balance)

                    WalletTransactions.objects.create(
                        wallet_balance=Decimal(0),
                        amount=used_amount_from_wallet,
                        transaction_type='debit',
                        user_id=int(user_id),
                        payment_details=payment_details
                    )

                session_start_time = timezone.make_aware(
                    datetime.combine(scheduling_date, scheduling.start_time))
                print(session_start_time)
                naive_datetime = datetime.now()
                aware_datetime = timezone.make_aware(
                    naive_datetime, timezone.get_current_timezone())
                Notifications.objects.create(user_id=scheduling.lawyer_profile.user.pk, title='User booked an appointment',
                                             description=f"session id:{appointment_obj.uuid} scheduled for time:{appointment_obj.session_start}", notify_time=aware_datetime)
                Notifications.objects.create(user_id=user_id, title='Session will Starts Now',
                                             description=f"Appoinment id:{appointment_obj.uuid} session will starts now", notify_time=session_start_time)
                Notifications.objects.create(user_id=scheduling.lawyer_profile.user.pk, title='Session will Starts Now',
                                             description=f"Appoinment id:{appointment_obj.uuid} session will starts now", notify_time=session_start_time)

                scheduling.is_listed = False
                scheduling.save()
                session_end_time = timezone.make_aware(
                    appointment_obj.session_end)
                print((session_end_time - timedelta(minutes=5)),
                      'this is the celery task scheduled time')
                celery_task_obj = send_money_to_the_lawyer_wallet.apply_async(
                    args=[scheduling.lawyer_profile.user.pk,
                          payment_details.pk, appointment_obj.pk],
                    eta=(session_end_time - timedelta(minutes=5))
                )
                CeleryTasks.objects.create(
                    appointment=appointment_obj, task_id=celery_task_obj.id)

        except Scheduling.DoesNotExist:
            print('Scheduling does not exist')
            return JsonResponse({'error': 'Scheduling not found'}, status=400)
        except Exception as e:
            print('Error occurred:', str(e))
            return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'status': 'success'}, status=200)

    def handle_wallet_payment(self, session):
        print('getting to the wallet working part....')
        user_id = session['metadata']['user_id']

        try:
            with transaction.atomic():
                payment_details = PaymentDetails.objects.create(
                    payment_method=session['payment_method_types'][0],
                    transaction_id=session['payment_intent'],
                    payment_for='wallet'
                )

                latest_transaction = WalletTransactions.objects.filter(
                    user_id=user_id).order_by('-created_at').first()

                latest_wallet_balance = latest_transaction.wallet_balance if latest_transaction else 0

                price = Decimal(session['amount_subtotal']) / 100
                latest_wallet_balance += Decimal(price)

                WalletTransactions.objects.create(
                    wallet_balance=latest_wallet_balance,
                    amount=price,
                    transaction_type='credit',
                    user_id=int(user_id),
                    payment_details=payment_details
                )

        except Exception as e:
            print('Error occurred:', str(e))
            return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'status': 'success'}, status=200)


class WalletAppointmentBooking(APIView):
    """
    API view to create a Wallet checkout session for booking an appointment.
    """
    permission_classes = [IsAuthenticated, VerifiedUser]

    def post(self, request, *args, **kwargs):
        try:
            scheduling_uuid = request.data.get('scheduling_uuid')
            scheduling_date_str = request.data.get('scheduling_date')
            print(scheduling_date_str, scheduling_uuid)

            user = request.user

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

            latest_transaction = WalletTransactions.objects.filter(
                user=user).order_by('-created_at').first()

            latest_wallet_balance = latest_transaction.wallet_balance if latest_transaction else 0

            if latest_wallet_balance < Decimal(scheduling.price):
                image_url = request.build_absolute_uri(
                    static('images/appointment.png'))
                if latest_wallet_balance == 0:
                    payment_method = ['card']
                    session_price = (int(scheduling.price * 100))
                else:
                    payment_method = ['card']
                    session_price = (int(scheduling.price * 100)) - \
                        (int(latest_wallet_balance*100))

                try:
                    checkout_session = stripe.checkout.Session.create(
                        payment_method_types=payment_method,
                        line_items=[
                            {
                                'price_data': {
                                    'currency': 'inr',
                                    'product_data': {
                                        'name': 'Appointment Schedule',
                                        'description':  f"{scheduling.lawyer_profile.user.full_name}'s session appointment",
                                        # 'images': [image_url],
                                    },
                                    'unit_amount': session_price,
                                },
                                'quantity': 1,
                            },
                        ],
                        mode='payment',
                        success_url=settings.DOMAIN_URL + \
                        'user/available-sessions/success?checkout_id={CHECKOUT_SESSION_ID}',
                        cancel_url=settings.DOMAIN_URL + 'user/available-sessions/fail',
                        metadata={
                            'scheduling_uuid': scheduling_uuid,
                            'scheduling_date': scheduling_date_str,
                            'user_id': self.request.user.id,
                            'payment_for': 'session-using-card-wallet',
                        }
                    )
                    print('payment processing with stripe going on')
                    return Response({'checkout_id': checkout_session.id}, status=status.HTTP_202_ACCEPTED)
                except Exception as e:
                    print('error with session saving')
                    print(e)
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            if not scheduling.is_listed or scheduling.is_canceled:
                print('session is not available now')
                return Response({'error': 'Session is not available now.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                with transaction.atomic():
                    scheduling_date = datetime.strptime(
                        scheduling_date_str, '%Y-%m-%d').date()
                    # lawyer_obj = scheduling.lawyer_profile.user
                    uuid_for_payment = uuid.uuid4()

                    payment_details = PaymentDetails.objects.create(
                        payment_method='wallet',
                        transaction_id=uuid_for_payment,
                        payment_for='session'
                    )

                    price = Decimal(scheduling.price)
                    latest_wallet_balance -= price

                    WalletTransactions.objects.create(
                        wallet_balance=latest_wallet_balance,
                        amount=price,
                        transaction_type='debit',
                        user=user,
                        payment_details=payment_details
                    )

                    appointment_obj = BookedAppointment.objects.create(
                        scheduling=scheduling,
                        user_profile=user,
                        session_start=datetime.combine(
                            scheduling_date, scheduling.start_time),
                        session_end=datetime.combine(
                            scheduling_date, scheduling.end_time),
                        payment_details=payment_details,
                    )
                    session_start_time = timezone.make_aware(
                        datetime.combine(scheduling_date, scheduling.start_time))
                    print(session_start_time)
                    print(timezone.now(), 'this is the time now')
                    naive_datetime = datetime.now()
                    aware_datetime = timezone.make_aware(
                        naive_datetime, timezone.get_current_timezone())
                    Notifications.objects.create(user_id=scheduling.lawyer_profile.user.pk, title='User booked an appointment',
                                                 description=f"session id:{appointment_obj.uuid} scheduled for time:{appointment_obj.session_start}", notify_time=aware_datetime)
                    Notifications.objects.create(user=user, title='Session will Starts Now',
                                                 description=f"Appoinment id:{appointment_obj.uuid} session will starts now", notify_time=session_start_time)
                    Notifications.objects.create(user_id=scheduling.lawyer_profile.user.pk, title='Session will Starts Now',
                                                 description=f"Appoinment id:{appointment_obj.uuid} session will starts now", notify_time=session_start_time)

                    scheduling.is_listed = False
                    scheduling.save()
                    session_end_time = timezone.make_aware(
                        appointment_obj.session_end)
                    print((session_end_time - timedelta(minutes=5)),
                          'this is the celery task scheduled time')
                    celery_task_obj = send_money_to_the_lawyer_wallet.apply_async(
                        args=[scheduling.lawyer_profile.user.pk,
                              payment_details.pk, appointment_obj.pk],
                        eta=(session_end_time - timedelta(minutes=5))
                    )
                    CeleryTasks.objects.create(
                        appointment=appointment_obj, task_id=celery_task_obj.id)
                    return JsonResponse({'status': 'success', 'checkout_id': uuid_for_payment}, status=200)
            except Scheduling.DoesNotExist:
                print('Scheduling does not exist')
                return JsonResponse({'error': 'Scheduling not found'}, status=400)

            except Exception as e:
                print('Error occurred:', str(e))
                return JsonResponse({'error': str(e)}, status=500)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookedAppointmentsListView(generics.ListAPIView):
    serializer_class = BookedAppointmentSerializer
    permission_classes = [IsAuthenticated, VerifiedUser]

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
                    is_completed=False,
                    is_canceled=False,
                ).filter(
                    # Q(session_date__gte=now.date()) & Q(scheduling__end_time__gte = now.time())
                    Q(session_end__gte=now)
                ).select_related('scheduling__lawyer_profile')

            elif query_param == 'completed':
                print('getting in to the lawyer finished')
                return BookedAppointment.objects.filter(
                    scheduling__lawyer_profile=lawyer_profile,
                    is_canceled=False,
                ).filter(
                    # Q(session_date__lte=now)
                    Q(session_end__lt=now)
                ).select_related('scheduling__lawyer_profile')

        elif user.role == 'user':
            if query_param == 'upcoming':
                print('getting in to the user upcoming')
                return BookedAppointment.objects.filter(
                    user_profile=user,
                    is_completed=False,
                    is_canceled=False,
                ).filter(
                    # Q(session_date__gte=now.date()) & Q(scheduling__end_time__gte = now.time())
                    Q(session_end__gte=now)
                ).select_related('scheduling__lawyer_profile')

            elif query_param == 'finished':
                # For users, show only past or completed appointments
                print('getting in to the user finished')
                return BookedAppointment.objects.filter(
                    user_profile=user,
                    is_canceled=False,
                ).filter(
                    Q(session_end__lt=now)
                    # Q(session_date__lt=now.date()) | (Q(session_date=now.date() )&Q(scheduling__end_time__lt = now.time())) # Ensure the session date is in the past
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
    permission_classes = [IsAdmin, VerifiedUser]
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
    permission_classes = [IsAdmin, VerifiedUser]

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
    permission_classes = [IsAdmin, VerifiedUser]
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
    permission_classes = [IsAdmin, VerifiedUser]
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


# cancelling the booked session
class CancelAppointmentView(APIView):
    permission_classes = [ObjectBasedUsers]

    def post(self, request, uuid):
        print(uuid)
        try:
            with transaction.atomic():
                appointment = BookedAppointment.objects.get(uuid=uuid)
                print(appointment)
                appointment.cancel()
                # appointment.scheduling.price
                latest_wallet_obj = WalletTransactions.objects.filter(
                    user=appointment.user_profile).order_by('-created_at').first()
                wallet_balance = latest_wallet_obj.wallet_balance if latest_wallet_obj else 0
                # price_for_lawyer = float(latest_wallet_obj.price) * 0.9
                latest_wallet_balance = (
                    Decimal(wallet_balance)+Decimal(appointment.scheduling.price))
                WalletTransactions.objects.create(
                    wallet_balance=latest_wallet_balance,
                    amount=Decimal(appointment.scheduling.price),
                    transaction_type='credit',
                    user=appointment.user_profile,
                    payment_details=appointment.payment_details
                )
                celery_task_obj = get_object_or_404(
                    CeleryTasks, appointment=appointment)
                if celery_task_obj:
                    current_app.control.revoke(
                        celery_task_obj.task_id, terminate=True)

            return Response({"message": "Appointment canceled successfully"}, status=status.HTTP_200_OK)
        except BookedAppointment.DoesNotExist:
            return Response({"error": "Appointment not found or you're not authorized to cancel this appointment"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BookedAppointmentDetailsView(generics.RetrieveAPIView):
    queryset = BookedAppointment.objects.all()
    permission_classes = [ObjectBasedUsers]
    serializer_class = BookedAppointmentSerializer
    lookup_field = 'uuid'


class SchedulingDeleteAPIView(generics.DestroyAPIView):
    queryset = Scheduling.objects.all()
    serializer_class = SchedulingSerializer

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.is_listed:
            self.perform_destroy(instance)
            return Response({"message": "Scheduling deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "Cannot delete this scheduling because it is already booked one."}, status=status.HTTP_400_BAD_REQUEST)
