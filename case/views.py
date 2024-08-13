# views.py
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics,status
from .models import CaseModels, UserCases
from .serializers import CaseModelsSerializer, UserCasesSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q


class CaseModelsListCreateView(generics.ListCreateAPIView):
    serializer_class = CaseModelsSerializer

    def get_queryset(self):
        queryset = CaseModels.objects.all()
        department_name = self.request.query_params.get('department_name', None)
        experience = self.request.query_params.get('experience', None)
        search_term = self.request.query_params.get('search_term', None)
        
        if department_name:
            queryset = queryset.filter(department__id__icontains=department_name)
        if experience:
            if experience == 'lessthan5':
                queryset = queryset.filter(lawyer__experience__lt=5)
            elif experience == '5-10':
                queryset = queryset.filter(lawyer__experience__gte=5, lawyer__experience__lte=10)
            elif experience == 'greaterthan10':
                queryset = queryset.filter(lawyer__experience__gt=10)
        
        if search_term:
            queryset = queryset.filter(lawyer__full_name__icontains=search_term)
        
        return queryset

class CaseModelsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CaseModels.objects.filter(is_listed=True).all()
    serializer_class = CaseModelsSerializer

# class UserCasesListCreateView(generics.ListCreateAPIView):
#     serializer_class = UserCasesSerializer

#     def get_queryset(self):
#         queryset = UserCases.objects.all()
#         user_id = self.request.query_params.get('user_id', None)
#         case_model_id = self.request.query_params.get('case_model_id', None)
#         search_term = self.request.query_params.get('search_term', None)

#         if user_id:
#             queryset = queryset.filter(user__id=user_id)
#         if case_model_id:
#             queryset = queryset.filter(case_model__id=case_model_id)
#         if search_term:
#             queryset = queryset.filter(subject__icontains=search_term)

#         return queryset



class UserCasesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data
        })


class UserCasesListCreateView(generics.ListCreateAPIView):
    serializer_class = UserCasesSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = UserCasesPagination

    def get_queryset(self):
        lawyer_id = self.request.user.id
        queryset = UserCases.objects.filter(case_model__lawyer__id=lawyer_id).order_by('created_at')

        case_model_id = self.request.query_params.get('case_model_id', None)
        search_term = self.request.query_params.get('search', None)  # Changed query param name to 'search'

        if case_model_id:
            queryset = queryset.filter(case_model__id=case_model_id)
        if search_term:
            queryset = queryset.filter(
                Q(subject__icontains=search_term) |
                Q(contact__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(context__icontains=search_term)
            )

        return queryset


class UserCasesDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserCasesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lawyer_id = self.request.user.id
        return UserCases.objects.filter(case_model__lawyer__id=lawyer_id)


class ChangeCaseStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            user_case = UserCases.objects.get(pk=pk, case_model__lawyer__id=request.user.id)
            user_case.is_accepted = not user_case.is_accepted
            user_case.save()
            return Response({'status': 'success', 'is_accepted': user_case.is_accepted}, status=status.HTTP_200_OK)
        except UserCases.DoesNotExist:
            return Response({'status': 'error', 'message': 'Case not found or permission denied'}, status=status.HTTP_404_NOT_FOUND)
        

# from rest_framework import generics
# from .models import CaseModels
# from .serializers import CaseModelsSerializer


# class CaseModelsListCreateView(generics.ListCreateAPIView):
#     serializer_class = CaseModelsSerializer

#     def get_queryset(self):
#         queryset = CaseModels.objects.all()
#         department_name = self.request.query_params.get('department_name', None)
#         experience = self.request.query_params.get('experience', None)
#         search_term = self.request.query_params.get('search_term', None)
#         # print(experience,'this is the experience')
#         if department_name:
#             queryset = queryset.filter(department__id__icontains=department_name)
#         if experience:
            
#             if experience == 'lessthan5':
#                 # print('entered into this')
#                 queryset = queryset.filter(lawyer__experience__lt=5)
#             elif experience == '5-10':
#                 queryset = queryset.filter(lawyer__experience__gte=5, lawyer__experience__lte=10)
#             elif experience == 'greaterthan10':
#                 queryset = queryset.filter(lawyer__experience__gt=10)
        
#         if search_term:
#             queryset = queryset.filter(lawyer__full_name__icontains=search_term)
        
#         return queryset
    

# class CaseModelsDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = CaseModels.objects.filter(is_listed=True).all()
#     serializer_class = CaseModelsSerializer
