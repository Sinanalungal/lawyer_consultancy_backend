from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WalletBalanceView, AddFundsView, WithdrawMoney, 
    WithdrawingRequestsViewSet, GetBalanceView
)

router = DefaultRouter()
router.register(r'withdrawal-requests', WithdrawingRequestsViewSet, basename='withdrawal-requests')

urlpatterns = [
    path('add-funds/', AddFundsView.as_view(), name='add-funds'),
    path('wallet-access/', GetBalanceView.as_view(), name='get-balance-and-history'),
    path('withdraw/', WithdrawMoney.as_view(), name='withdraw-money'),
    path('wallet-balance-access/', WalletBalanceView.as_view(), name='get-wallet-balance'),
    path('', include(router.urls)),
]
