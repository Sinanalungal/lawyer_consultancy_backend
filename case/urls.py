from django.urls import path
from .views import CaseListCreateView,CreateAllotedCaseView,CaseFinished,UserAllotedCasesView, CaseDetailView,StateListView,CaseListView,UnlistCaseView,SelectedCasesView

urlpatterns = [
    path('cases/', CaseListCreateView.as_view(), name='case-list-create'),
    path('cases/<int:pk>/', CaseDetailView.as_view(), name='case-detail'),
    path('states/', StateListView.as_view(), name='state-list'),
    path('case-for-lawyers/', CaseListView.as_view(), name='case-list'),
    path('cases-manage/<int:pk>/unlist/', UnlistCaseView.as_view(), name='unlist-case'),
    path('selected-cases/<int:case_id>/', SelectedCasesView.as_view(), name='selected-cases-list'),  
    path('selected-cases/', SelectedCasesView.as_view(), name='create-selected-case'),
    path('alloted-cases/create/', CreateAllotedCaseView.as_view(), name='create-alloted-case'),
    path('alloted-cases/my-cases/', UserAllotedCasesView.as_view(), name='user-alloted-cases'),
    path('approve-finished/<int:pk>/', CaseFinished.as_view(), name='unlist-case'),
]


