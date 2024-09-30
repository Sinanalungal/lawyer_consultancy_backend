from django.urls import path
from . import views

urlpatterns = [
    path('add-schedule/', views.SchedulingCreateView.as_view(), name='schedule-create'),
    path('user-sessions/', views.UserSessionsView.as_view(), name='lawyer-sessions'),
    path('active/', views.ActiveSchedulesView.as_view(), name='active-schedules'),
    # path('cancel/<uuid:uuid>/', views.CancelScheduleView.as_view(), name='cancel-schedule'),
    path('schedules/', views.AvailableSlotsView.as_view(), name='available-slots'),
    path('book-appointment/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('appointments/', views.BookedAppointmentsListView.as_view(), name='booked-appointments-list'),
    path('all-scheduling/', views.SchedulingListViewForAdmin.as_view(), name='scheduling-list'),
    path('schedule/update/<int:pk>/', views.SchedulingUpdateViewAdmin.as_view(), name='scheduling-update'),
    path('successfull-appointments/', views.SuccessFullSessionReportView.as_view(), name='successfull-ppointments'),
    path('pdf-downloading-data/', views.ForDownloadDataFetching.as_view(), name='pdf-downloading-data/'),
    path('cancel-appointments/<str:uuid>/', views.CancelAppointmentView.as_view(), name='cancel-appointment'),
    path('details-of-appointment/<str:uuid>/',views.BookedAppointmentDetailsView.as_view(),name='details-of-appointment'),
    path('book-wallet-appointment/', views.WalletAppointmentBooking.as_view(), name='book_wallet_appointment'),
    path('scheduled-session/<int:pk>/delete/', views.SchedulingDeleteAPIView.as_view(), name='scheduling-delete'),
]
