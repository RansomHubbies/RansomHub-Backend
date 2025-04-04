from django.db import models
from users.models import CustomUser

# create a model to store the messages between users
class Message(models.Model):

    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sender")
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="recipient")
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message}"

# create a model to store the group information
class Group(models.Model):
    
    username = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(CustomUser)

    def __str__(self):
        return self.username
    
class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message}"
    
class MessageMedia(models.Model):
    
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sender_media")
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="recipient_media")
    media = models.FileField(upload_to="media/")
    MEDIA_CHOICES = [
        ("image", "image"),
        ("video", "video"),
        ("audio", "audio"),
        ("document", "document"),
    ]
    media_type = models.CharField(max_length=255, choices=MEDIA_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.message}: {self.media}"
