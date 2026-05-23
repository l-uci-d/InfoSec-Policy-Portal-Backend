from django.db import models
from django.conf import settings

# Create your models here.
class Notification(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_notifs', on_delete=models.CASCADE, null=True)
    action = models.CharField(max_length=255)
    document = models.ForeignKey('documents.Document', related_name='related_notifs', on_delete=models.CASCADE, null=True)
    misc_title = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserNotification(models.Model):
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_notifs', on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, related_name='user_notifs', on_delete=models.CASCADE)
    read = models.BooleanField(default=False)