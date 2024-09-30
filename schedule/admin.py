from django.contrib import admin
from . import models
admin.site.register(models.Scheduling)
admin.site.register(models.BookedAppointment)
admin.site.register(models.PaymentDetails)
admin.site.register(models.CeleryTasks)