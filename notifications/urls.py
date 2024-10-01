from django.urls import path
from . import views

urlpatterns = [
    path('recent-notifications/',views.NotificationListView.as_view(),name='recent-notifications'),
    path('notifications-count/',views.NotificationCountView.as_view(),name='notifications-count')
]
