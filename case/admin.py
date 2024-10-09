from django.contrib import admin
from .models import Case,SelectedCases,AllotedCases

admin.site.register(Case)
admin.site.register(SelectedCases)
admin.site.register(AllotedCases)