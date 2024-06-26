from django.urls import path
from . import views

urlpatterns = [
   path('subscription_models/',views.AdminSubscriptionView.as_view(),name='subscription_models'),
   path('lawyer_subscription_plans/',views.LawyerSubscriptionView.as_view(),name='lawyer_subscription_models'),
   path('all_subscription_plan_models/',views.AllSubscriptionModelPlansView.as_view(),name='all_subscription_plan_models'),
   path('lawyer_plans/<int:lawyer_id>',views.SubscriptionPlanAPIView.as_view(),name='lawyer_plans'),
   path('create-checkout-session/',views.CheckoutSession.as_view(),name='checkout-sesssion'),
   path('available-subscriptions/', views.SubscriptionListView.as_view(), name='subscription-available'),
   path('webhook/',views.WebhookView.as_view(),name='webhook_view'),
]
