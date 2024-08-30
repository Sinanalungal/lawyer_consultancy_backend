from django.urls import path
from .views import CaseListCreateView, CaseDetailView,StateListView,CaseListView,UnlistCaseView

urlpatterns = [
    path('cases/', CaseListCreateView.as_view(), name='case-list-create'),
    path('cases/<int:pk>/', CaseDetailView.as_view(), name='case-detail'),
    path('states/', StateListView.as_view(), name='state-list'),
    path('case-for-lawyers/', CaseListView.as_view(), name='case-list'),
    path('cases-manage/<int:pk>/unlist/', UnlistCaseView.as_view(), name='unlist-case'),
]



# from django.urls import path
# from .views import CaseModelsListCreateView, CaseModelsDetailView, UserCasesListCreateView, UserCasesDetailView,ChangeCaseStatusView

# urlpatterns = [
#     path('cases-list/', CaseModelsListCreateView.as_view(), name='case-list-create'),
#     path('cases-list/<int:pk>/', CaseModelsDetailView.as_view(), name='case-detail'),
#     path('user-cases/', UserCasesListCreateView.as_view(), name='user-cases-list-create'),
#     path('user-cases/<int:pk>/', UserCasesDetailView.as_view(), name='user-cases-detail'),
#     path('user-cases/<int:pk>/change-status/', ChangeCaseStatusView.as_view(), name='change-case-status'),

# ]



# # from django.urls import path
# # from .views import CaseModelsListCreateView, CaseModelsDetailView

# # urlpatterns = [
# #     path('cases-list/', CaseModelsListCreateView.as_view(), name='case-list-create'),
# #     path('cases-list/<int:pk>/', CaseModelsDetailView.as_view(), name='case-detail'),
# # ]
