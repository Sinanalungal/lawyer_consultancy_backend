from django.urls import path
from .views import AddLawyerView


urlpatterns = [
   path('add-lawyer/', AddLawyerView.as_view(), name='add-lawyer'),
]
