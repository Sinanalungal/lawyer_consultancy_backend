from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.Blog)
admin.site.register(models.Comment)
admin.site.register(models.Like)
admin.site.register(models.Report)
admin.site.register(models.Saved)