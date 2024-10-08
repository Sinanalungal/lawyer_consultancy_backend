from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AddFundsView, WithdrawMoney, WithdrawingRequestsViewSet, WithdrawFundsView, GetBalanceView

router = DefaultRouter()
router.register(r'withdrawal-requests', WithdrawingRequestsViewSet)

urlpatterns = [
    path('add-funds/', AddFundsView.as_view(), name='add-funds'),
    # path('withdraw-funds/', WithdrawFundsView.as_view(), name='withdraw-funds'),
    path('wallet-access/', GetBalanceView.as_view(), name='get-balance'),  # Changed name to avoid conflict
    path('withdraw/', WithdrawMoney.as_view(), name='withdraw-money'),
    path('', include(router.urls)), 
]
