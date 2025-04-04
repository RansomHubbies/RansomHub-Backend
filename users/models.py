from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import random

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=10, null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)
    otp = models.CharField(max_length=6, blank=True, null=True) 
    is_approved = models.BooleanField(default=False)
    public_key = models.CharField(max_length=256, null=False, blank=False, default="sdkhgvs7dyi6sgbskdmgb")
    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
        help_text="The groups this user belongs to."
    )
    is_suspended = models.BooleanField(default=False)
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_set",
        blank=True,
        help_text="Specific permissions for this user."
    )
    def __str__(self):
        return self.email
    
    def generate_otp(self):
        """Generates a 6-digit OTP"""
        self.otp = str(random.randint(100000, 999999))
        self.save()



