from django.db import models
from api.models import CustomUser,LawyerProfile,States

class TimeStampedModel(models.Model):
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Case(TimeStampedModel):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        # ('Rejected', 'Rejected'),
    ]

    case_type = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.PositiveIntegerField() 
    state= models.ForeignKey(States,on_delete=models.CASCADE)
    # state = models.CharField(max_length=50)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reference_until = models.DateField()
    is_listed = models.BooleanField(default=True)

    def __str__(self):
        return self.case_type

    class Meta:
        # indexes = [
        #     models.Index(fields=['status']),
        #     models.Index(fields=['reference_until']),
        # ]
        ordering = ['-created_time']  # Optional: Default ordering by created_time descending

class SelectedCases(models.Model):
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE)
    case_model = models.ForeignKey(Case, on_delete=models.CASCADE)
    is_selected = models.BooleanField(default=False)


# from django.db import models
# from api.models import CustomUser, Department

# class CaseModels(models.Model):
#     lawyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cases')
#     department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='cases')
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     is_listed = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True) 

#     def __str__(self):
#         return f"Case by {self.lawyer} in {self.department}"

# class UserCases(models.Model):
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_cases')
#     subject = models.CharField(max_length=50, blank=False, null=False)
#     email = models.EmailField(null=False, blank=False)
#     contact = models.CharField(max_length=10, null=False, blank=False)
#     context = models.TextField()
#     case_model = models.ForeignKey(CaseModels, on_delete=models.CASCADE, related_name='user_cases')
#     created_at = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
#     is_accepted = models.BooleanField(default=False, blank=False)
#     paid = models.BooleanField(default=False, blank=False)
    
#     def __str__(self):
#         return f"User Case: {self.subject} by {self.user}"