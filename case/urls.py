from django.urls import path
from .views import CaseModelsListCreateView, CaseModelsDetailView, UserCasesListCreateView, UserCasesDetailView,ChangeCaseStatusView

urlpatterns = [
    path('cases-list/', CaseModelsListCreateView.as_view(), name='case-list-create'),
    path('cases-list/<int:pk>/', CaseModelsDetailView.as_view(), name='case-detail'),
    path('user-cases/', UserCasesListCreateView.as_view(), name='user-cases-list-create'),
    path('user-cases/<int:pk>/', UserCasesDetailView.as_view(), name='user-cases-detail'),
    path('user-cases/<int:pk>/change-status/', ChangeCaseStatusView.as_view(), name='change-case-status'),

]



# from django.urls import path
# from .views import CaseModelsListCreateView, CaseModelsDetailView

# urlpatterns = [
#     path('cases-list/', CaseModelsListCreateView.as_view(), name='case-list-create'),
#     path('cases-list/<int:pk>/', CaseModelsDetailView.as_view(), name='case-detail'),
# ]
