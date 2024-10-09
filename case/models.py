from django.db import models
from api.models import CustomUser, LawyerProfile, States


class TimeStampedModel(models.Model):
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Case(TimeStampedModel):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Outdated', 'Outdated'),
    ]

    case_type = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.PositiveIntegerField()
    state = models.ForeignKey(States, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='Pending')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reference_until = models.DateField()
    is_listed = models.BooleanField(default=True)

    def __str__(self):
        return self.case_type

    class Meta:

        ordering = ['-created_time']


class SelectedCases(models.Model):
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE)
    case_model = models.ForeignKey(Case, on_delete=models.CASCADE)
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class AllotedCases(models.Model):

    STATUS_CHOICES = [
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
    ]
    selected_case = models.OneToOneField(
        SelectedCases, on_delete=models.CASCADE, related_name='alloted_case')
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='Ongoing')
    created_at = models.DateTimeField(auto_now_add=True)
