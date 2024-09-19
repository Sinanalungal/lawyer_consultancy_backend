from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from api.models import LawyerProfile
from .serializers import LawyerProfileSerializer
from django.db.models import Q
from server.permissions import VerifiedUser


class VerifiedLawyerProfileListView(generics.ListAPIView):
    serializer_class = LawyerProfileSerializer
    permission_classes = [IsAuthenticated,VerifiedUser]

    def get_queryset(self):
        queryset = LawyerProfile.objects.filter(user__is_verified=True).all()

        search = self.request.query_params.get('search', None)
        print(search)
        if search:
            queryset = queryset.filter(
                Q(user__full_name__icontains=search) |
                Q(departments__department_name__icontains=search) |
                Q(languages__name__icontains=search)
            ).distinct()
        
        department = self.request.query_params.get('department', None)
        print(department)
        if department and department != "All":
            queryset = queryset.filter(departments__pk=department)
        
        language = self.request.query_params.get('language', None)
        print(language)
        if language and language != "All":
            
            queryset = queryset.filter(languages__pk=language)

        experience = self.request.query_params.get('experience', None)
        print(experience)
        if experience and experience != "All":
            if experience=="Less than five":
                queryset = queryset.filter(experience_lt=5)
            elif experience=="In between five to ten":
                queryset = queryset.filter(experience__gte=5, experience__lte=10)
            elif experience=="Greater than ten":
                queryset = queryset.filter(experience__gt=10)

 

        return queryset
