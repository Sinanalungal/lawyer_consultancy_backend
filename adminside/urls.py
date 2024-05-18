from django.urls import path,include
from .views import CustomUserViewSet,BlogViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'blogs', BlogViewSet)

urlpatterns = [
   path('user-data/', CustomUserViewSet.as_view({'get': 'list','patch':'block'}), name='user-data-list'),
   path('', include(router.urls)),
]
