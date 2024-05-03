from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
        ('lawyer', 'Lawyer'),
    )
    full_name = models.CharField(max_length=100,blank=False,null=False)
    email = models.EmailField(unique=True)
    phone_number= models.CharField(max_length=10,blank=False,null=False,unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_verified = models.BooleanField(default=True)
    