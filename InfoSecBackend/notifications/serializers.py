from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['notifications_id', 'module', 'to_user_id', 'message', 'notifications_status', 'created_at']