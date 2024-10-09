from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.UserGrowthView.as_view(), name='admin-dashboard'),
    path('lawyer-dashboard/', views.LawyerDashboardView.as_view(),
         name='lawyer-dashboard'),
]
