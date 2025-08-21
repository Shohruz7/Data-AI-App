from django.db import models
from django.conf import settings

class DataSet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Chat(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats')
    title = models.CharField(max_length=200)
    saved = models.BooleanField(default=False)
    last_dataset = models.ForeignKey(DataSet, null=True, blank=True, on_delete=models.SET_NULL, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.user})"


class ChatMessage(models.Model):
    MESSAGE_TYPES = (
        ('analysis', 'Analysis'),
        ('question', 'Question'),
    )
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    type = models.CharField(max_length=16, choices=MESSAGE_TYPES)
    content = models.TextField()
    response = models.TextField(null=True, blank=True)
    chart = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.chat.title} - {self.type} @ {self.created_at}"