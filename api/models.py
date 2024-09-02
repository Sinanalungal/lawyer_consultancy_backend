from django.contrib.auth.models import AbstractUser
from django.db import models

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
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10, null=True, blank=True, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.full_name



class Department(models.Model):
    """
    Model for storing department information.
    """
    department_name = models.CharField(max_length=30, unique=True)

    def __str__(self) -> str:
        return self.department_name

class Language(models.Model):
    """
    Model to store languages.

    Fields:
    - name: The name of the language.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name
    


class States(models.Model):
    """
    Model to store states.
    """
    name = models.CharField(max_length=100, blank=True, null=True)

class LawyerProfile(models.Model):
    """
    Model to store lawyer-specific fields.

    Fields:
    - user: OneToOneField to CustomUser
    - departments: ManyToManyField to Department
    - experience: PositiveIntegerField for years of experience
    - description: TextField for a brief description
    - languages: ManyToManyField to Language
    - address: CharField for address
    - city: CharField for city
    - state: CharField for state
    - postal_code: CharField for postal code
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='lawyer_profile')
    departments = models.ManyToManyField(Department, blank=True)
    experience = models.PositiveIntegerField(default=0, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    languages = models.ManyToManyField(Language, blank=True)
    
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    # state = models.ForeignKey(States,on_delete=models.CASCADE)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    

    def __str__(self) -> str:
        return f"Profile for {self.user.email}"



class PasswordResetToken(models.Model):
    """
    Model to store password reset tokens for users.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self) -> str :
        return f"Token for {self.user.email}"


