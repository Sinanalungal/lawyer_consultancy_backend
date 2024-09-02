from django.urls import path
from .views import AddFundsView, WithdrawFundsView,GetBalanceView

urlpatterns = [
    path('add-funds/', AddFundsView.as_view(), name='add-funds'),
    path('withdraw-funds/', WithdrawFundsView.as_view(), name='withdraw-funds'),
    path('wallet-access/', GetBalanceView.as_view(), name='add-funds'),
]
