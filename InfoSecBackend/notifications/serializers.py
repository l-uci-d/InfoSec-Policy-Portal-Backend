from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source='document.title')
    actor_name = serializers.SerializerMethodField()
    def get_actor_name(self, obj):
        return f"{obj.actor.first_name} {obj.actor.last_name}"
    class Meta:
        model = Notification
        fields = ['actor', 'action', 'document', 'created_at', 'document_title', 'actor_name', 'misc_title']