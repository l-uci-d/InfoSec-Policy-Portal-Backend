from django.db import models

# Create your models here.
class Notification(models.Model):
    notifications_id = models.CharField(primary_key=True, max_length=255)
    module = models.CharField(max_length=255)
    to_user_id = models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    notifications_status = models.CharField(max_length=255)
    created_at = models.DateTimeField()

    #class Meta:
     #   db_table = 'admin"."notifications'