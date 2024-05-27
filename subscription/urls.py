from django.urls import path
from . import views

urlpatterns = [
   path('subscription_models/',views.AdminSubscriptionView.as_view(),name='subscription_models')
]
