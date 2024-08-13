from django.urls import path
from . import views

urlpatterns = [
    path('add-schedule/', views.SchedulingCreateView.as_view(), name='schedule-create'),
    path('user-sessions/', views.UserSessionsView.as_view(), name='lawyer-sessions'),
    path('active/', views.ActiveSchedulesView.as_view(), name='active-schedules'),
    path('cancel/<uuid:uuid>/', views.CancelScheduleView.as_view(), name='cancel-schedule'),
]
