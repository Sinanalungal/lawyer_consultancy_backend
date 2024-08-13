from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from server.permissions import IsLawyer
from django.core.exceptions import ValidationError
from .models import Scheduling
from .serializers import SchedulingSerializer,ScheduledSerializer
from api.models import LawyerProfile
from rest_framework.views import APIView


class SchedulingCreateView(generics.CreateAPIView):
    queryset = Scheduling.objects.all()
    serializer_class = SchedulingSerializer
    permission_classes = [IsLawyer]

    def perform_create(self, serializer):
        user_email = self.request.user.email
        print(user_email)
        try:
            lawyer_profile = LawyerProfile.objects.get(user__email=user_email)
        except LawyerProfile.DoesNotExist:
            raise ValidationError("No LawyerProfile associated with the current user.")
        serializer.save(lawyer_profile=lawyer_profile)
        

    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



class UserSessionsView(generics.ListAPIView):
    serializer_class = ScheduledSerializer
    permission_classes = [IsLawyer]
    pagination_class = None  


    def get_queryset(self):
        user = self.request.user.email
        return Scheduling.objects.filter(lawyer_profile__user__email=user, is_completed=False, is_canceled=False)
    

# from rest_framework.pagination import PageNumberPagination

# class CustomPagination(PageNumberPagination):
#     page_size = 2

class ActiveSchedulesView(generics.ListAPIView):
    serializer_class = ScheduledSerializer
    permission_classes = [IsLawyer]
    # pagination_class = CustomPagination  


    def get_queryset(self):
        user = self.request.user.email
        return Scheduling.objects.filter(lawyer_profile__user__email=user, is_completed=False, is_canceled=False)
    

class CancelScheduleView(generics.UpdateAPIView):
    permission_classes = [IsLawyer]
    queryset = Scheduling.objects.all()
    lookup_field = 'uuid'
    
    def update(self, request, *args, **kwargs):
        schedule = self.get_object()
        if schedule.is_canceled:
            return Response({'detail': 'This schedule is already canceled.'}, status=status.HTTP_400_BAD_REQUEST)
        
        schedule.is_canceled = True
        schedule.save()
        return Response({'detail': 'Schedule canceled successfully.'}, status=status.HTTP_200_OK)