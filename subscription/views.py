from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from .serializers import SubscriptionPlanModelsSerializer
from .models import SubscriptionPlanModels
from django.db.models import Q

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
