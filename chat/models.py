from django.db import models
from users.models import CustomUser

# create a model to store the messages between users
class Message(models.Model):
    
    sender = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message}"

# create a model to store the group information
class Group(models.Model):
    
    username = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, unique=True)
    members = models.ManyToManyField(CustomUser)

    def __str__(self):
        return self.name
