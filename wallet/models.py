from django.db import models
from api.models import CustomUser 
from schedule.models import PaymentDetails

class WalletTransactions(models.Model):
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    payment_details = models.ForeignKey(PaymentDetails, on_delete=models.CASCADE, null=True, blank=True)
    wallet_balance = models.DecimalField(max_digits=12,decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} of {self.amount} on {self.created_at}"
