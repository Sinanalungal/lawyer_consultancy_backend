import uuid
from django.db import models
from api.models import LawyerProfile,CustomUser
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError

class Scheduling(models.Model):
    # uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    reference_until = models.DateField()
    lawyer_profile = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE)
    is_listed = models.BooleanField(default=True)
    is_canceled = models.BooleanField(default=False)

    def clean(self):
        if not self.date:
            raise ValidationError('Date must be provided.')
        
        if not self.start_time:
            raise ValidationError('Start time must be provided.')
        
        # now = datetime.now().time()
        # today = datetime.today().date()

        # if self.date == today and self.start_time <= now:
        #     raise ValidationError('Start time must be later than the current time for today.')

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
        return f'Scheduling on {self.date} from {self.start_time} to {self.end_time} with uuid {self.pk}'

class PaymentDetails(models.Model):
    payment_method = models.CharField(max_length=50) 
    transaction_id = models.CharField(max_length=100, null=False, blank=False)
    payment_for = models.CharField(max_length=50,null=False,blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f'{self.transaction_id}:{self.created_at}'


class BookedAppointment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    scheduling = models.ForeignKey(Scheduling, on_delete=models.CASCADE)
    user_profile = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  
    session_date = models.DateTimeField(default=None, null=True, blank=True) 
    booked_at = models.DateTimeField(auto_now_add=True)
    is_transaction_completed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    payment_details = models.OneToOneField(PaymentDetails, on_delete=models.CASCADE, null=True, blank=True)
    
    
def clean(self):
    if not self.scheduling:
        raise ValidationError('Scheduling must be provided.')

    if not self.user_profile:
        raise ValidationError('User must be provided.')

    if self.scheduling.is_canceled or not(self.scheduling.is_listed):
        raise ValidationError('Cannot book an appointment for a canceled or completed schedule.')

    now = datetime.now()

    # Parse session_date if it's a string
    if isinstance(self.session_date, str):
        try:
            self.session_date = datetime.fromisoformat(self.session_date)
        except ValueError:
            raise ValidationError('Invalid session date format.')

    # Ensure the session_date is within the valid period
    if not (self.scheduling.date <= now.date() <= self.scheduling.reference_until):
        raise ValidationError('Session date is not within the valid period.')

    # Check if booking is for a future time
    if (self.session_date.date() == now.date() and self.session_date.time() <= now.time()) :
        raise ValidationError('Cannot book an appointment for a past time.')
    
    def __str__(self):
        return f'Booked Appointment for {self.user_profile} on {self.scheduling.date} at {self.scheduling.start_time}'