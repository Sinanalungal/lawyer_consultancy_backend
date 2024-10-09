from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from .filters import CaseFilter
from .models import Case, SelectedCases, AllotedCases
from .serializers import (
    CaseSerializer,
    StateSerializer,
    AllotedCasesSerializer,
    SelectedCasesSerializer
)
from api.models import States, LawyerProfile


class CaseListCreateView(generics.ListCreateAPIView):
    serializer_class = CaseSerializer

    def get_queryset(self):
        user = self.request.user
        selected_filter = self.request.query_params.get('selected', 'all')

        if user.is_authenticated:
            # Mark outdated cases
            Case.objects.filter(
                user=user,
                is_listed=True,
                status='Pending',
                reference_until__lt=timezone.now()
            ).update(status='Outdated')

            # Base queryset
            queryset = Case.objects.filter(user=user, is_listed=True).filter(
                Q(status='Pending') | Q(status='Outdated')
            )

            # Determine if a case is selected
            selected_cases_subquery = SelectedCases.objects.filter(
                case_model=OuterRef('pk')
            )

            if selected_filter == 'selected':
                queryset = queryset.filter(
                    Exists(selected_cases_subquery)
                )
            elif selected_filter == 'unselected':
                queryset = queryset.filter(
                    ~Exists(selected_cases_subquery)
                )

            return queryset

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
    page_size = None


class StateListView(generics.ListAPIView):
    serializer_class = StateSerializer
    queryset = States.objects.all()
    pagination_class = NoPagination


class CaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer


class CaseListView(generics.ListAPIView):
    serializer_class = CaseSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CaseFilter

    def get_queryset(self):
        lawyer = self.request.user
        obj = LawyerProfile.objects.filter(user=lawyer).first()
        queryset = Case.objects.filter(Q(is_listed=True) & Q(status='Pending'))

        selected_case_ids = SelectedCases.objects.filter(
            lawyer=obj).values_list('case_model_id', flat=True)
        queryset = queryset.exclude(id__in=selected_case_ids)

        today = timezone.now().date()
        print(today)
        queryset = queryset.filter(reference_until__gte=today)

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


class SelectedCasesView(generics.GenericAPIView):
    queryset = SelectedCases.objects.all()
    serializer_class = SelectedCasesSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        case_id = request.query_params.get("case_id")
        print(case_id)
        if case_id:
            selected_cases = self.queryset.filter(case_model_id=case_id)
            serializer = self.get_serializer(selected_cases, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Case ID not provided"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lawyer = LawyerProfile.objects.filter(user=request.user).first()
        if not lawyer:
            return Response({"detail": "Lawyer profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        case_model_id = serializer.validated_data['case_model'].id

        if SelectedCases.objects.filter(lawyer=lawyer, case_model_id=case_model_id).exists():
            return Response({"detail": "This case has already been selected by the lawyer"}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer, lawyer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer, lawyer):
        serializer.save(lawyer=lawyer)


class CreateAllotedCaseView(generics.CreateAPIView):
    serializer_class = AllotedCasesSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        selected_case_id = request.data.get('selected_case_id')

        try:
            selected_case = SelectedCases.objects.get(id=selected_case_id)
            case_model = Case.objects.get(id=selected_case.case_model.pk)
        except SelectedCases.DoesNotExist:
            return Response({'error': 'Selected case not found'}, status=status.HTTP_404_NOT_FOUND)

        if selected_case.case_model.user != request.user:
            return Response({'error': 'You are not authorized to assign this case'}, status=status.HTTP_403_FORBIDDEN)

        alloted_case = AllotedCases.objects.create(
            selected_case=selected_case,
            status=request.data.get('status', 'Ongoing')
        )
        # case_model.is_listed = False
        case_model.status = 'Accepted'
        case_model.save()

        serializer = self.get_serializer(alloted_case)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserAllotedCasesView(generics.ListAPIView):
    serializer_class = AllotedCasesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Fetching only the cases related to the authenticated user
        query_set = AllotedCases.objects.filter(
            Q(selected_case__lawyer__user=self.request.user) |
            Q(selected_case__case_model__user=self.request.user)
        )

        # Getting search and status parameters from query params
        search_term = self.request.query_params.get('search', None)
        status = self.request.query_params.get('status', None)

        if search_term:
            query_set = query_set.filter(
                Q(selected_case__case_model__case_type__icontains=search_term)
                # | Q(selected_case__lawyer__user__full_name__icontains=search_term)
            )

        # Filter by status if provided
        if status:
            query_set = query_set.filter(status=status)

        return query_set


class CaseFinished(generics.UpdateAPIView):
    queryset = AllotedCases.objects.filter(status='Ongoing').all()
    # serializer_class = CaseSerializer

    def patch(self, request, *args, **kwargs):
        case = self.get_object()
        case.status = 'Completed'
        case.save()
        return Response({"detail": "Case has marked as completed successfully."}, status=status.HTTP_200_OK)


class AllotedCasesListView(generics.ListAPIView):
    queryset = AllotedCases.objects.all()
    serializer_class = AllotedCasesSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status']
    search_fields = [
        'selected_case__case_model__case_type',
        'selected_case__case_model__user__email',
        'selected_case__lawyer__user__full_name'
    ]

    def get_queryset(self):
        """
        Optionally restricts the returned results by filtering against
        the status passed in the query string.
        """
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status).order_by('-created_at')
        return queryset
