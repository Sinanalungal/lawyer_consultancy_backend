from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from server.permissions import IsAdmin
from api.models import CustomUser
from .serializer import CustomUserSerializer
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class CustomUserViewSet(viewsets.ViewSet):
    """
    A viewset for managing CustomUser instances.
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = CustomPagination
    
    def list(self, request):
        """
        List all CustomUser instances or filter by role if role parameter is provided.

        Args:
            request: The request object.

        Returns:
            Response: Serialized data of CustomUser instances.
        """
        role_param = request.query_params.get('role')
        search_param = request.query_params.get('search')
        status_param = request.query_params.get('isVerified')
        print(role_param)
        print(search_param)
        print(status_param)

        def boolsetting(status_param):
            if status_param == "true":
                return True
            elif status_param == "false":
                return False
            
        if role_param and search_param != '':
            if status_param == 'all':
                queryset = CustomUser.objects.filter(role=role_param).filter(Q(full_name__icontains=search_param)|Q(email__icontains=search_param)|Q(phone_number__icontains=search_param)).order_by('id')
            else:
                queryset = CustomUser.objects.filter(role=role_param).filter(Q(full_name__icontains=search_param)|Q(email__icontains=search_param)|Q(phone_number__icontains=search_param)).filter(is_verified=boolsetting(status_param)).order_by('id')
        elif role_param and search_param == '':
            if status_param == 'all':
                queryset = CustomUser.objects.filter(role=role_param).all().order_by('id')
            else:
                queryset = CustomUser.objects.filter(role=role_param).filter(is_verified=boolsetting(status_param)).all().order_by('id')
        paginator=self.pagination_class()
        result_page =  paginator.paginate_queryset(queryset,request)
        # print(result_page)
        serializer = CustomUserSerializer(result_page, many=True)
        # print(serializer.data)
        # print(paginator.get_paginated_response(serializer.data))
        return paginator.get_paginated_response(serializer.data)

    def block(self, request):
        """
        Block or unblock a CustomUser instance based on provided data.

        Args:
            request: The request object containing data for blocking/unblocking.

        Returns:
            Response: Serialized data of CustomUser instances after blocking/unblocking.
        """
        try:
            role = request.data.get('role')
            params = request.data.get('id')
            print(params)
            user = CustomUser.objects.get(id=params)
            user.is_verified = not user.is_verified
            serializer = CustomUserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                queryset = CustomUser.objects.filter(role=role).order_by('id')
                serializer_data = CustomUserSerializer(queryset, many=True)
                return Response(serializer_data.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'message': 'give a valid data'}, status=status.HTTP_404_NOT_FOUND)
