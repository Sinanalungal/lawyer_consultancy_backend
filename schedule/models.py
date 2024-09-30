import uuid
from django.db import models
from api.models import LawyerProfile,CustomUser
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone


class Scheduling(models.Model):
    # uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    # reference_until = models.DateField()
    lawyer_profile = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE)
    is_listed = models.BooleanField(default=True)
    is_canceled = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if not self.date:
            raise ValidationError('Date must be provided.')
        
        if not self.start_time:
            raise ValidationError('Start time must be provided.')
        
        
        if self.end_time <= self.start_time:
            raise ValidationError('End time must be later than start time.')

        start_datetime = datetime.combine(self.date, self.start_time)
        end_datetime = datetime.combine(self.date, self.end_time)
        if (end_datetime - start_datetime) < timedelta(minutes=30):
            raise ValidationError('End time must be at least 30 minutes after start time.')

        if not (1 <= self.price <= 1000):
            raise ValidationError('Price must be between 1 and 1000.')
        
        if self.pk is None: 
            conflicting_schedules = Scheduling.objects.filter(
                lawyer_profile=self.lawyer_profile,
                date=self.date,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )
            if conflicting_schedules.exists():
                raise ValidationError("This time slot conflicts with an existing schedule.")

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
    session_start = models.DateTimeField(default=None, null=True, blank=True)
    session_end = models.DateTimeField(default=None, null=True, blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)
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

        now = timezone.now()

        if isinstance(self.session_start, str):
            try:
                self.session_start = datetime.fromisoformat(self.session_start)
            except ValueError:
                raise ValidationError('Invalid session date format.')

        if not (self.scheduling.date < now.date()):
            raise ValidationError('Session date is not within the valid period.')

        if (self.session_start.date() == now.date() and self.session_start.time() <= now.time()):
            raise ValidationError('Cannot book an appointment for a past time.')

    def cancel(self):
        if self.is_canceled:
            raise ValidationError("This appointment is already canceled.")
        if self.session_start < timezone.now():
            raise ValidationError("Cannot cancel a past appointment.")
        
        self.is_canceled = True
        scheduling_obj = self.scheduling
        scheduling_obj.is_listed =True
        scheduling_obj.save()

        self.save()
    def __str__(self):
        return f'Booked Appointment for {self.user_profile} on {self.scheduling.date} at {self.scheduling.start_time}'
    
class CeleryTasks(models.Model):
    appointment = models.ForeignKey(BookedAppointment,on_delete=models.CASCADE)
    task_id = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"{self.task_id} - {self.appointment.uuid}"