from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from .serializers import SubscriptionPlanModelsSerializer,SubscriptionPlanSerializer
from .models import SubscriptionPlanModels,SubscriptionPlan
from django.db.models import Q
from rest_framework.generics import ListAPIView
from api.models import CustomUser


class AdminSubscriptionView(APIView):
    class SubscriptionPlanPagination(PageNumberPagination):
        page_size = 5  # Number of items to return per page
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
    def get(self, request, lawyer_id, format=None):
        subscription_plans = SubscriptionPlan.objects.filter(lawyer__id=lawyer_id,valid=True).all()
        print('-----------------')
        if not subscription_plans.exists():
            return Response({'detail': 'No subscription plans found for the specified lawyer.'}, status=status.HTTP_404_NOT_FOUND)
        
        serialize=SubscriptionPlanSerializer(subscription_plans, many=True)

        # Return the subscription plans data as a JSON response
        return Response(serialize.data, status=status.HTTP_200_OK)