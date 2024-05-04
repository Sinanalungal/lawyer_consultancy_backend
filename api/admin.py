from django.contrib import admin
from .models import CustomUser,PasswordResetToken

admin.site.register(CustomUser)
admin.site.register(PasswordResetToken)