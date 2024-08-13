from django.db import models
from api.models import CustomUser, Department

class CaseModels(models.Model):
    lawyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cases')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='cases')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_listed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"Case by {self.lawyer} in {self.department}"

class UserCases(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_cases')
    subject = models.CharField(max_length=50, blank=False, null=False)
    email = models.EmailField(null=False, blank=False)
    contact = models.CharField(max_length=10, null=False, blank=False)
    context = models.TextField()
    case_model = models.ForeignKey(CaseModels, on_delete=models.CASCADE, related_name='user_cases')
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
    is_accepted = models.BooleanField(default=False, blank=False)
    paid = models.BooleanField(default=False, blank=False)
    
    def __str__(self):
        return f"User Case: {self.subject} by {self.user}"