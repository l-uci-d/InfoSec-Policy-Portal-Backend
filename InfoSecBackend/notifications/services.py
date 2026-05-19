from .models import Notification, UserNotification
from datetime import datetime
from django.contrib.auth import get_user_model

def create_notif(actor, action, document):
    new_notif = Notification(actor=actor, action=action, document=document)
    new_notif.save()
    users_list = get_user_model().objects.all()
    UserNotification.objects.bulk_create([UserNotification(to_user=user, notification=new_notif) for user in users_list])