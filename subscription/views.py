from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status,generics
import stripe.error
from .serializers import SubscriptionPlanModelsSerializer,SubscriptionPlanSerializer,SubscriptionSerializer
from .models import SubscriptionPlanModels,SubscriptionPlan,Subscription
from django.db.models import Q
from rest_framework.generics import ListAPIView
from api.models import CustomUser
import stripe
from django.conf import settings
from rest_framework.permissions import IsAuthenticated 
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from django.core.mail import send_mail
from chat.models import Thread


class AdminSubscriptionView(APIView):
    class SubscriptionPlanPagination(PageNumberPagination):
        page_size = 5 
        page_size_query_param = 'page_size'
        max_page_size = 100

    def get(self, request, *args, **kwargs):
        try:
            search_query = request.query_params.get('search', '')
            if search_query:
                data_result = SubscriptionPlanModels.objects.filter(
                    Q(name__icontains=search_query) |
                    Q(billing_cycle__icontains=search_query) |
                    Q(description__icontains=search_query)
                ).order_by('-id')
            else:
                data_result = SubscriptionPlanModels.objects.all().order_by('-id')
                
            paginator = self.SubscriptionPlanPagination()
            page = paginator.paginate_queryset(data_result, request)
            if page is not None:
                serializer = SubscriptionPlanModelsSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                serializer = SubscriptionPlanModelsSerializer(data_result, many=True)
                return Response(serializer.data)
        except SubscriptionPlanModels.DoesNotExist:
            return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        serializer = SubscriptionPlanModelsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AllSubscriptionModelPlansView(ListAPIView):
    queryset = SubscriptionPlanModels.objects.all().order_by('-id')
    serializer_class = SubscriptionPlanModelsSerializer


class LawyerSubscriptionView(APIView):
    class SubscriptionPlanPagination(PageNumberPagination):
        page_size = 5  
        page_size_query_param = 'page_size'
        max_page_size = 100

    def get(self, request, *args, **kwargs):
        try:
            user_id = request.query_params.get('id')
            search_query = request.query_params.get('search', '')
            valid_bool = request.query_params.get('valid', 'all')
            print(valid_bool)

            if valid_bool == 'all':
                if search_query:
                    print('-----------all is working-----------')
                    data_result = SubscriptionPlan.objects.filter(
                        lawyer__id=user_id
                    ).filter(
                        Q(plan__name__icontains=search_query) | Q(plan__billing_period__icontains=search_query)
                    ).order_by('-id')

                else:
                    data_result = SubscriptionPlan.objects.filter(lawyer__id=user_id).order_by('-id')
            else:
                if valid_bool =='true':
                    valid_bool=True
                else:
                    valid_bool=False
                    
                if search_query:
                    print('entering------------------')
                    data_result = SubscriptionPlan.objects.filter(
                        lawyer__id=user_id ,valid=valid_bool
                    ).filter(
                        Q(plan__name__icontains=search_query) | Q(plan__billing_period__icontains=search_query)
                    ).order_by('-id')

                else:
                    data_result = SubscriptionPlan.objects.filter(lawyer__id=user_id,valid=valid_bool).order_by('-id')

            paginator = self.SubscriptionPlanPagination()
            page = paginator.paginate_queryset(data_result, request)
            if page is not None:
                serializer = SubscriptionPlanSerializer(page, many=True, context={"request": request})
                return paginator.get_paginated_response(serializer.data)
            else:
                serializer = SubscriptionPlanSerializer(data_result, many=True, context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        try:
            lawyer_id = request.data.get('lawyer_id')
            plan_id = request.data.get('subscription_plan_id')
            price = request.data.get('price')

            lawyer = CustomUser.objects.get(id=lawyer_id)
            plan = SubscriptionPlanModels.objects.get(id=plan_id)

            if SubscriptionPlan.objects.filter(lawyer__id=lawyer_id, plan__id=plan_id, price=price).exists():
                return Response({"error": "Plan already exists"}, status=status.HTTP_400_BAD_REQUEST)
            
            subscription_plan = SubscriptionPlan.objects.create(
                lawyer=lawyer,
                plan=plan,
                price=price
            )

            serializer = SubscriptionPlanSerializer(subscription_plan, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except CustomUser.DoesNotExist:
            return Response({"error": "Lawyer not found"}, status=status.HTTP_404_NOT_FOUND)
        
        except SubscriptionPlanModels.DoesNotExist:
            return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def patch(self, request, *args, **kwargs):
        try:
            plan_id = request.data.get('plan_id')
            lawyer_id = request.data.get('lawyer_id')
            subscription_id = request.data.get('subscription_id')
            subscription = SubscriptionPlan.objects.filter(lawyer__id=lawyer_id, plan__id=plan_id, id=subscription_id).first()
            if not subscription:
                return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)
            if subscription.valid == False:
                existing_valid_subscription = SubscriptionPlan.objects.filter(
                    lawyer__id=lawyer_id, plan__id=plan_id, valid=True
                ).exclude(id=subscription_id).exists()

                if existing_valid_subscription:
                    return Response({"error": "An active subscription with this plan already exists"}, status=status.HTTP_400_BAD_REQUEST)
                subscription.valid = True
                subscription.save()
            elif subscription.valid == True:
                subscription.valid = False
                subscription.save()
            serializer = SubscriptionPlanSerializer(subscription, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class SubscriptionPlanAPIView(APIView):
    def post(self, request, lawyer_id, format=None):

        user_id=request.data.get('user_id')
        data=Subscription.objects.filter(user__id=user_id,plan__lawyer__id=lawyer_id,status = 'active')
        # threads_of_the_user = Thread.objects.by_user(user=request.user)
        # lawyer_obj = CustomUser.objects.get(id=lawyer_id)
        # # print(lawyer_obj,'lawyer_obj')
        # threads_of_the_lawyer = Thread.objects.by_user(user = lawyer_obj)
        thread_in_both= Thread.objects.involving_both_users(user1_id=user_id,user2_id =lawyer_id)
        # print(thread_in_both.first(),'this is the thread in both user and laawyer')
        # print(threads_of_the_user,'threads of the user')
        # print(threads_of_the_lawyer,'threads of the lawyer')

        if data.exists():
            if data.first().end_date > timezone.now():
                return Response({"detail": "You already have a plan with this lawyer"}, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                data_obj = data.first()
                data_obj.status = 'inactive'
                data_obj.save()
                thread_of_the_lawyer_and_user = Thread.objects.involving_both_users(user1_id=user_id,user2_id =lawyer_id).first()
                thread_of_the_lawyer_and_user.is_listed = False
                thread_of_the_lawyer_and_user.save()
                
        subscription_plans = SubscriptionPlan.objects.filter(lawyer__id=lawyer_id,valid=True).all()
        # print('-----------------')
        if not subscription_plans.exists():
            return Response({'detail': 'No subscription plans found for the specified lawyer.'}, status=status.HTTP_404_NOT_FOUND)
        
        serialize=SubscriptionPlanSerializer(subscription_plans, many=True)

        # Return the subscription plans data as a JSON response
        return Response(serialize.data, status=status.HTTP_200_OK)
    


stripe.api_key =  settings.STRIPE_API_KEY

class CheckoutSession(APIView):
    def post(self, request, *args, **kwargs):
        print('entering into checkout')
        subscription_id = request.data.get('subscription_id')
        lawyer_id = request.data.get('lawyer_id')
        user_id = request.data.get('user_id')
        print(lawyer_id)
        
        subscription = SubscriptionPlan.objects.filter(id=subscription_id, valid=True).first()
        subscription_name = subscription.plan.name
        subscription_price = int(subscription.price * 100)  # Price in paise (e.g., ₹20.00)

        try:
            # Create a checkout session with price data and metadata
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': subscription_name,
                            },
                            'unit_amount': subscription_price,
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=settings.DOMAIN_URL + 'user?success=true&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.DOMAIN_URL + f'user/subscription/{lawyer_id}?canceled=true',
                metadata={
                    'subscription_id': subscription_id,
                    'user_id': user_id,
                }
            )
            print('success')
        except Exception as e:
            print('failed')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        print(checkout_session.id)
        return Response(checkout_session.id, status=status.HTTP_200_OK)
    


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    endpoint_secret = 'whsec_e883094ce98575db46ef700f91d94786f4b4cec88e05d6c7c3cc7c753e5543cd'
    print('request_comes................')
    def fulfill_order(self, session, subscription_metadata):
        # print(session, subscription_metadata, 'this is the session and metadata from fulfill order')
        print("Fulfilling order")
        user_id = subscription_metadata.get('user_id')
        plan_id = subscription_metadata.get('subscription_id')
        print(user_id,plan_id, 'this is the user')

        try:
            user = CustomUser.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except (CustomUser.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
            print(f"Error retrieving user or plan: {e}")
            return

        if session.payment_status == "paid":
            start_date = timezone.now()
            end_date = start_date + timezone.timedelta(days=30)  # Assuming 30 days for a monthly plan, adjust accordingly
            renewal_date = end_date

            print('This is the Session: ',session)

            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                renewal_date=renewal_date,
                status='active',
                payment_method=session.get('payment_method_types')[0],
                transaction_id=session.get('payment_intent'),
                payment_status=session.get('payment_status'),
                created_by=user,
            )
            subscribed_lawyer = CustomUser.objects.filter(id=plan.lawyer.pk).first()
            print(subscribed_lawyer,'this is subscribed lawyer object')
            thread_qs = Thread.objects.involving_both_users(user1_id=user_id,user2_id=plan.lawyer.pk)
            print(thread_qs,'this is thread qs')
            if (thread_qs.exists()):
                print('entered in to the inside')
                thread_obj=thread_qs.first()
                print(thread_obj.is_listed)
                thread_obj.is_listed = True
                print(thread_obj,'this is the updated threaad obj')
                thread_obj.save()
            else:
                thread_obj=Thread.objects.create(first_person=user,second_person=subscribed_lawyer)
            # print(thread_obj,'this is thread')
            print("Subscription created:", subscription)
            send_mail(
                'Your Transaction Is Successfull',
                'Your latest subscription transaction is success , Enjoy the subscription features !',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

        # try:
        #     subscription = Subscription.objects.get(transaction_id=session.payment_intent)
        #     subscription.status = 'active'
        #     subscription.payment_status = 'paid'
        #     subscription.save()
        #     print("Subscription fulfilled and marked as active.")
        # except Subscription.DoesNotExist:
        #     print("Subscription not found.")
        
    # def create_order(self, session, subscription_metadata):
    #     print(session, subscription_metadata, 'this is the session and metadata from create order')    
    #     print("Creating order")

    #     user_id = subscription_metadata.get('user_id')
    #     plan_id = subscription_metadata.get('plan_id')

    #     try:
    #         user = CustomUser.objects.get(id=user_id)
    #         plan = SubscriptionPlan.objects.get(id=plan_id)
    #     except (CustomUser.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
    #         print(f"Error retrieving user or plan: {e}")
    #         return

    #     if session.payment_status == "paid":
    #         start_date = timezone.now()
    #         end_date = start_date + timezone.timedelta(days=30)  # Assuming 30 days for a monthly plan, adjust accordingly
    #         renewal_date = end_date

    #         subscription = Subscription.objects.create(
    #             user=user,
    #             plan=plan,
    #             start_date=start_date,
    #             end_date=end_date,
    #             renewal_date=renewal_date,
    #             status='active',
    #             payment_method=session.get('payment_method_types')[0],
    #             transaction_id=session.get('payment_intent'),
    #             payment_status=session.get('payment_status'),
    #             created_by=user,
    #         )
    #         print("Subscription created:", subscription)
        
    def email_customer_about_failed_payment(self, session, subscription_metadata):
        # print(session, subscription_metadata, 'this is the session and metadata from email customer about failed payment')       
        user_id = subscription_metadata.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            email = user.email
        except CustomUser.DoesNotExist as e:
            print(f"Error retrieving user or plan: {e}")
            return
 
        print("Emailing customer")
        send_mail(
            'Transaction Failed',
            'Your latest subscription transaction is failed , please try again',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        # try:
        #     subscription = Subscription.objects.get(transaction_id=session.payment_intent)
        #     subscription.payment_status = 'failed'
        #     subscription.status = 'canceled'
        #     subscription.cancellation_date = timezone.now()
        #     subscription.save()
        #     print("Subscription marked as failed and canceled.")
        # except Subscription.DoesNotExist:
        #     print("Subscription not found.")
        
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        event = None

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.endpoint_secret)
        except ValueError as e:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            return HttpResponse(status=400)
        
        # print("Received event: ", event)
        
        session = None
        if event['type'] in ['checkout.session.completed', 'checkout.session.async_payment_succeeded', 'checkout.session.async_payment_failed']:
            session_id = event['data']['object']['id']
            try:
                session = stripe.checkout.Session.retrieve(session_id, expand=['line_items'])
            except stripe.error.InvalidRequestError as e:
                print(f"Error retrieving session {session_id}: {e}")
                return HttpResponse(status=400)

        if session:
            subscription_metadata = session.metadata
            print(subscription_metadata,'this is a subscription metadata')

            if event['type'] == 'checkout.session.completed':
                # self.create_order(session, subscription_metadata)
                if session.payment_status == "paid":
                    self.fulfill_order(session, subscription_metadata)

            elif event['type'] == 'checkout.session.async_payment_succeeded':
                self.fulfill_order(session, subscription_metadata)

            elif event['type'] == 'checkout.session.async_payment_failed':
                self.email_customer_about_failed_payment(session, subscription_metadata)
        
        return HttpResponse(status=200)

class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Subscription.objects.filter(user=user).filter(status = 'active')