from django.db import models
from api.models import CustomUser,Department

# Create your models here.

class CaseModels(models.Model):
    lawyer = models.ForeignKey(CustomUser,blank=False,null=False ,on_delete=models.CASCADE)
    department = models.ForeignKey(Department,null=False,blank=False, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_listed = models.BooleanField(default=True)