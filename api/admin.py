from django.contrib import admin
from .models import CustomUser,PasswordResetToken,Department

admin.site.register(CustomUser)
admin.site.register(PasswordResetToken)
admin.site.register(Department)