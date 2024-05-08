from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from server.permissions import IsAdmin
from api.models import CustomUser
from .serializer import CustomUserSerializer


class CustomUserViewSet(viewsets.ViewSet):
    """
    A viewset for managing CustomUser instances.
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def list(self, request):
        """
        List all CustomUser instances or filter by role if role parameter is provided.

        Args:
            request: The request object.

        Returns:
            Response: Serialized data of CustomUser instances.
        """
        role_param = request.query_params.get('role')
        if role_param:
            queryset = CustomUser.objects.filter(role=role_param).order_by('id')
        else:
            queryset = CustomUser.objects.all().order_by('id')
        serializer = CustomUserSerializer(queryset, many=True)
        return Response(serializer.data)

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
