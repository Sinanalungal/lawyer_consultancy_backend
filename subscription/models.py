from django.db import models
from api.models import CustomUser
# Create your models here.

class SubscriptionPlanModels(models.Model):
    BILLING_PERIOD_CHOICES = [
        ('day', 'Day'),
        ('month', 'Month'),
        ('year', 'Year'),
    ]
    name = models.CharField(max_length=100)
    billing_cycle = models.IntegerField()
    billing_period = models.CharField(max_length=10, choices=BILLING_PERIOD_CHOICES)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    # features = models.JSONField()
    description = models.TextField()

    def __str__(self) -> str:
        return self.name


class SubscriptionPlan(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    lawyer = models.ForeignKey(CustomUser,null=False,blank=False , on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlanModels, null=False, blank=False, on_delete=models.CASCADE, related_name='subscriptions')
    valid = models.BooleanField(default=False,null=False, blank=False)

    def __str__(self) -> str:
        return f'{self.lawyer.email} - {self.plan.name}'



class Subscription(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    renewal_date = models.DateTimeField()
    cancellation_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)  # e.g., 'active', 'pending', 'canceled'
    payment_method = models.CharField(max_length=50)  # e.g., 'credit card', 'paypal'
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(max_length=20)  # e.g., 'paid', 'pending', 'failed'
    created_by = models.ForeignKey(CustomUser, related_name='created_subscriptions', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(null=True, blank=True)
        
