from django.urls import path,include
from .views import AddLawyerView
from rest_framework.routers import DefaultRouter


# router = DefaultRouter()
# router.register(r'blogs', BlogViewSet)
# router.register(r'add-department', DepartmentViewSet)

urlpatterns = [
   # path('user-data/', CustomUserViewSet.as_view({'get': 'list','patch':'block'}), name='user-data-list'),
   # path('add-lawyer/', AddLawyerView.as_view(), name='add-lawyer'),
   # # path('add-department/', DepartmentViewSet.as_view(), name='add-department'),
   # path('', include(router.urls)),
   path('add-lawyer/', AddLawyerView.as_view(), name='add-lawyer'),
]
