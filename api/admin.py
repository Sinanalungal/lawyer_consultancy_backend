from django.contrib import admin
from .models import CustomUser,PasswordResetToken,Department,Language,LawyerProfile

admin.site.register(CustomUser)
admin.site.register(PasswordResetToken)
admin.site.register(Department)
admin.site.register(Language)
admin.site.register(LawyerProfile)
