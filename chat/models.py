# from django.db import models
# from django.contrib.auth.models import User

# class ChatChannel(models.Model):
#     name = models.CharField(max_length=255, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)

# class Message(models.Model):
#     channel = models.ForeignKey(ChatChannel, on_delete=models.CASCADE)
#     sender = models.ForeignKey(User, on_delete=models.CASCADE)
#     content = models.TextField()  # This can be encrypted content
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.sender.username}: {self.content}"
