from django.db import models
from api.models import CustomUser

# class NotificationStatus(models.TextChoices):
#     PENDING = 'pending', 'Pending'
#     SENT = 'sent', 'Sent'
#     FAILED = 'failed', 'Failed'

class Notifications(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=False, blank=False)
    title = models.CharField(max_length=100)
    description = models.TextField()
    notify_time = models.DateTimeField()
    # status = models.CharField(max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-notify_time']  
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.title} - {self.user.username}"
