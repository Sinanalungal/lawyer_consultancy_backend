from django.urls import path
from .views import CustomUserViewSet

urlpatterns = [
   path('user-data/', CustomUserViewSet.as_view({'get': 'list','patch':'block'}), name='user-data-list'),
]
