from django.contrib.auth.models import AbstractUser
from django.db import models

class Department(models.Model):

    department_name = models.CharField(max_length=30, null=False, blank=False, unique=True)

    def __str__(self):
        return self.department_name

class CustomUser(AbstractUser):
    """
    Custom user model extending AbstractUser.
    
    Fields:
    - full_name: CharField
    - email: EmailField
    - phone_number: CharField
    - role: CharField (choices: 'user', 'admin', 'lawyer')
    - is_verified: BooleanField (default: True)
    """
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
        ('lawyer', 'Lawyer'),
    )
    full_name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10,null=True ,blank=False,default=None, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    profile=models.ImageField(upload_to='profile/',default=None, blank=False ,null=True)
    is_verified = models.BooleanField(default=True)
    #----------------------------------------------------------------------------------------------#
    document=models.ImageField(upload_to='lawyer_doc/',default=None, blank=False ,null=True)
    departments = models.ManyToManyField(Department,default=None, blank=False )
    experience = models.PositiveIntegerField(default=0, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    #----------------------------------------------------------------------------------------------#

class PasswordResetToken(models.Model):
    """
    Model to store password reset tokens for users.
    
    Fields:
    - user: OneToOneField to CustomUser
    - token: CharField
    - created_at: DateTimeField (auto-generated on creation)
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     """
    #     Return the email of the associated user for string representation.
    #     """
    #     return self.user.email
