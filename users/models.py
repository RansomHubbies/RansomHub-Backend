from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
import random

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    is_approved= models.BooleanField(default=False)
    phone = models.CharField(max_length=10, null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)
    verification_docs = models.ImageField(upload_to="verification_docs/", null=True, blank=True)
    otp = models.CharField(max_length=6, blank=True, null=True) 
    public_key = models.CharField(max_length=256, null=False, blank=False)
    encrypted_private_key = models.CharField(max_length=256, null=False, blank=False)
    private_key_salt = models.CharField(max_length=256, null=False, blank=False)
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


    followers = models.ManyToManyField('self', symmetrical=False, related_name='following_me', blank=True)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followed_by_me', blank=True)
    blocked_users = models.ManyToManyField('self', symmetrical=False, related_name='blocked_by', blank=True)
    follow_requests = models.ManyToManyField('self', symmetrical=False, related_name='requested_to_follow', blank=True)
    
    last_block_time = models.DateTimeField(null=True, blank=True)
    block_action_count = models.IntegerField(default=0)

    def __str__(self):
        return self.email
    
    def generate_otp(self):
        """Generates a 6-digit OTP"""
        self.otp = str(random.randint(100000, 999999))
        self.save()



