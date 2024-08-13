import uuid
from django.db import models
from api.models import LawyerProfile
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError

class Scheduling(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    reference_until = models.DateField()
    lawyer_profile = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)

    def clean(self):
        now = datetime.now().time()
        today = datetime.today().date()

        if self.date == today and self.start_time <= now:
            raise ValidationError('Start time must be later than the current time for today.')

        if self.end_time <= self.start_time:
            raise ValidationError('End time must be later than start time.')

        start_datetime = datetime.combine(self.date, self.start_time)
        end_datetime = datetime.combine(self.date, self.end_time)
        if (end_datetime - start_datetime) < timedelta(minutes=30):
            raise ValidationError('End time must be at least 30 minutes after start time.')

        if not (1 <= self.price <= 1000):
            raise ValidationError('Price must be between 1 and 1000.')

        if self.reference_until < self.date:
            raise ValidationError('Reference Until date must be on or after the start date.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'Scheduling on {self.date} from {self.start_time} to {self.end_time} with uuid {self.uuid}'
