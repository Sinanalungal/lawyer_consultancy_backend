from django.urls import path
from . import views

urlpatterns = [
    path('add-schedule/', views.SchedulingCreateView.as_view(), name='schedule-create'),
    path('user-sessions/', views.UserSessionsView.as_view(), name='lawyer-sessions'),
    path('active/', views.ActiveSchedulesView.as_view(), name='active-schedules'),
    path('cancel/<uuid:uuid>/', views.CancelScheduleView.as_view(), name='cancel-schedule'),
    path('schedules/', views.AvailableSlotsView.as_view(), name='available-slots'),
    path('book-appointment/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('appointments/', views.BookedAppointmentsListView.as_view(), name='booked-appointments-list'),
    path('all-scheduling/', views.SchedulingListViewForAdmin.as_view(), name='scheduling-list'),
    path('schedule/update/<int:pk>/', views.SchedulingUpdateViewAdmin.as_view(), name='scheduling-update'),
]
