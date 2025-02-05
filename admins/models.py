from django.db import models
from users.models import CustomUser

class Admin(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    is_super_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username



