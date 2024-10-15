from django.urls import path
from . import views

urlpatterns = [
    path('lawyers/', views.VerifiedLawyerProfileListView.as_view(), name='lawyer-profile-detail'),
]
