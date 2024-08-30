from rest_framework import generics 
from rest_framework.response import Response
from rest_framework import status
from .models import Case
from .serializers import CaseSerializer,StateSerializer
from api.models import States
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import CaseFilter

class CaseListCreateView(generics.ListCreateAPIView):
    serializer_class = CaseSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned cases to the ones related to the logged-in user.
        """
        user = self.request.user
        if user.is_authenticated:
            return Case.objects.filter(user=user).filter(is_listed=True)
        return Case.objects.none() 

    def post(self, request, *args, **kwargs):
        print(request.data) 
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Save the case with the user set to the currently logged-in user.
        """
        serializer.save(user=self.request.user)




class NoPagination(PageNumberPagination):
    page_size = None  # This disables pagination

class StateListView(generics.ListAPIView):
    serializer_class = StateSerializer
    queryset = States.objects.all()
    pagination_class = NoPagination  # Use the NoPagination class to disable pagination



class CaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer



class CaseListView(generics.ListAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CaseFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = self.request.query_params.get('search', None)
        if search_term:
            queryset = queryset.filter(case_type__icontains=search_term)
        return queryset



class UnlistCaseView(generics.UpdateAPIView):
    queryset = Case.objects.filter(is_listed=True).all()
    serializer_class = CaseSerializer

    def delete(self, request, *args, **kwargs):
        case = self.get_object()
        case.is_listed = False
        case.save()
        return Response({"detail": "Case has been unlisted successfully."}, status=status.HTTP_200_OK)